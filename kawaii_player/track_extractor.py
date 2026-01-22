import json
import subprocess
import os
import hashlib
import threading
import time
import mimetypes

class TrackExtractor:
    """Service for extracting and managing MKV tracks"""
    
    def __init__(self, ui):
        self.ui  = ui
        self.cache_dir = os.path.join(ui.home_folder, "tmp")
        self.transcode_jobs = {}  # Track ongoing transcodes
        self.transcode_status = {}
        self.cache_path_mapping = {}
        self.estimated_file_size = {}
        self.webm_transcoder = self.ui.webm_transcoder

    def _is_chrome_browser(self, user_agent):
        """Detect Chrome from user agent"""
        if not user_agent:
            return False
        user_agent = user_agent.lower()
        return 'chrome' in user_agent or 'chromium' in user_agent

    def _is_browser_compatible_video(self, codec):
        """Check if video codec is browser-compatible for MP4 container"""
        # H.264 (avc1/h264) and H.265 (hevc) are widely supported in MP4
        # VP9 and AV1 have good support in modern browsers
        compatible_codecs = ['h264', 'avc1', 'h265', 'vp9', 'av1']
        return codec.lower() in compatible_codecs

    def _is_audio_browser_playable(self, codec):
        """Check if audio codec can be played directly in browsers"""
        # These codecs are widely supported across modern browsers
        browser_playable = ['aac', 'mp3', 'opus', 'vorbis', 'flac']
        return codec.lower() in browser_playable

    def _is_raspberry_pi(self):
        """Check if running on Raspberry Pi"""
        try:
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
            kernel = result.stdout.strip()
            
            if 'rpt-rpi' not in kernel and 'raspi' not in kernel:
                return False
            
            self.ui.logger.info(f"Detected Raspberry Pi (kernel: {kernel})")
            return True
            
        except Exception as e:
            self.ui.logger.error(f"Error detecting RPi: {e}")
            return False

    def _check_hw_encoder_available(self):
        """Check if hardware encoder is available (cached result)"""
        if hasattr(self, '_hw_encoder_checked') and self._hw_encoder_checked:
            return self._hw_encoder_available
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            self._hw_encoder_available = 'h264_v4l2m2m' in result.stdout
            self._hw_encoder_checked = True
            
            if self._hw_encoder_available:
                self.ui.logger.info("Hardware encoder (h264_v4l2m2m) detected!")
            else:
                self.ui.logger.info("No hardware encoder found")
                
            return self._hw_encoder_available
            
        except Exception as e:
            self.ui.logger.error(f"Error checking hardware encoder: {e}")
            self._hw_encoder_checked = True
            self._hw_encoder_available = False
            return False

    def _get_optimal_transcode_settings(self, source_codec = None):
        """Get optimal transcoding settings for RPi 4B"""
        if not self._is_raspberry_pi():
            return {
                'encoder': 'libx264',
                'preset': 'veryfast',
                'crf': '23',
                'threads': '0',
                'maxrate': '5M',
                'bufsize': '10M',
                'profile': 'main',
                'level': '4.0',
                'pix_fmt': 'yuv420p',
            }

        self.ui.logger.info("RPi 4B software encoding - ultrafast 480p")
        return {
            'encoder': 'libx264',
            'preset': 'ultrafast',
            'crf': '28',
            'threads': '4',
            'profile': 'baseline',
            'level': '3.1',
            'pix_fmt': 'yuv420p',
            'scale': '-2:480',
            'use_hw': False
        }
        
    # ===========================
    # VIDEO TRANSCODING
    # ===========================

    def _generate_cache_key(self, video_index, audio_index):
        """Generate consistent cache key"""
        if audio_index is not None:
            self.ui.logger.info(f"aid:{audio_index} selected")
        return str(video_index)
    
    def start_audio_extraction(self, mkv_path, audio_index):
        """Start audio extraction job and return immediate response"""
        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}
        
        # Check if audio needs transcoding
        info = self.get_mkv_info(mkv_path)
        needs_transcode = True
        
        if info and info.get('audio'):
            for aud in info['audio']:
                if aud['index'] == audio_index:
                    audio_codec = aud.get('codec', '')
                    needs_transcode = not self._is_audio_browser_playable(audio_codec)
                    break
        
        # Generate cache filename
        operation = 'transcode' if needs_transcode else 'extract'
        cache_filename = self._get_cache_filename(mkv_path, 'audio', audio_index, operation)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # Check if already processed
        if os.path.exists(cache_path):
            file_size = os.path.getsize(cache_path)
            if file_size > 1024:
                return {
                    'success': True,
                    'url': f'/cache/{cache_filename}',
                    'status': 'completed',
                    'progress': 100,
                    'size': file_size
                }
        
        # Job key
        job_key = f"{mkv_path}_audio_{audio_index}"
        
        # Check if processing is in progress
        if job_key in self.transcode_jobs and self.transcode_jobs[job_key]['status'] in ['processing', 'completed', 'starting']:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0)
            }
        
        # Start new job in background
        self.transcode_jobs[job_key] = {
            'status': 'starting',
            'progress': 0,
            'output_path': cache_path,
            'started_at': time.time(),
            'cached_path': self.get_cached_filename(cache_filename)
        }

        thread = threading.Thread(
                target=self._extract_audio_worker,
            args=(mkv_path, audio_index, cache_path, job_key, needs_transcode)
        )
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'url': f'/cache/{cache_filename}',
            'status': 'processing',
            'progress': 0,
            'message': 'Audio extraction started'
        }

    def _extract_audio_worker(self, mkv_path, track_index, output_path, job_key, transcode=False):
        """Background worker for audio extraction with progress"""
        process = None
        try:
            # Get duration
            duration = self._get_video_duration(mkv_path)
            
            # Build command
            if transcode:
                # Check if RPi for optimized settings
                if self._is_raspberry_pi():
                    cmd = [
                        'ffmpeg',
                        '-i', mkv_path,
                        '-map', f'0:{track_index}',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-ar', '44100',
                        '-ac', '2',
                        '-movflags', '+frag_keyframe+empty_moov+default_base_moof',
                        '-f', 'mp4',
                        '-progress', 'pipe:1',
                        '-y',
                        output_path
                    ]
                else:
                    cmd = [
                        'ffmpeg',
                        '-i', mkv_path,
                        '-map', f'0:{track_index}',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-ar', '48000',
                        '-movflags', '+frag_keyframe+empty_moov+default_base_moof',
                        '-f', 'mp4',
                        '-progress', 'pipe:1',
                        '-y',
                        output_path
                    ]
            else:
                cmd = [
                    'ffmpeg',
                    '-i', mkv_path,
                    '-map', f'0:{track_index}',
                    '-c:a', 'copy',
                    '-progress', 'pipe:1',
                    '-y',
                    output_path
                ]
            
            self.ui.logger.info(f"Starting audio extraction: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
                bufsize=1
            )
            
            # Store process in job
            self.transcode_jobs[job_key]['process'] = process
            self.transcode_jobs[job_key]['status'] = 'processing'
            
            # Parse progress
            self._parse_ffmpeg_progress(process, job_key, duration)
            
            # Wait for completion
            process.wait()
            
            # Check result
            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.transcode_jobs[job_key].update({
                    'status': 'completed',
                    'progress': 100,
                    'size': file_size
                })
                self.ui.logger.info(f"Audio extraction completed: {output_path}")
            else:
                self.transcode_jobs[job_key].update({
                    'status': 'failed',
                    'error': f'FFmpeg failed with code {process.returncode}'
                })
                
        except Exception as e:
            self.ui.logger.error(f"Error in audio extraction worker: {e}")
            self.transcode_jobs[job_key].update({
                'status': 'failed',
                'error': str(e)
            })
        finally:
            if job_key in self.transcode_jobs and 'process' in self.transcode_jobs[job_key]:
                del self.transcode_jobs[job_key]['process']

    def get_audio_extraction_status(self, mkv_path, audio_index):
        """Get status of ongoing audio extraction"""
        operation = 'transcode'  # Assume transcode for status check
        cache_filename = self._get_cache_filename(mkv_path, 'audio', audio_index, operation)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        job_key = f"{mkv_path}_audio_{audio_index}"
        
        # Check if actively processing
        if job_key in self.transcode_jobs:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0)
            }
        
        # Check if completed
        if os.path.exists(cache_path):
            file_size = os.path.getsize(cache_path)
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': 'completed',
                'progress': 100,
                'size': file_size
            }
        
        return {
            'success': False,
            'status': 'not_found'
        }

    def _estimate_transcoded_file_size(self, duration, video_bitrate='1500k', audio_bitrate='128k'):
        """Estimate final transcoded file size based on duration and bitrates"""
        try:
            # Parse bitrates (handle 'k' and 'M' suffixes)
            def parse_bitrate(bitrate_str):
                if isinstance(bitrate_str, (int, float)):
                    return bitrate_str
                bitrate_str = str(bitrate_str).lower()
                if 'm' in bitrate_str:
                    return float(bitrate_str.replace('m', '')) * 1000
                elif 'k' in bitrate_str:
                    return float(bitrate_str.replace('k', ''))
                return float(bitrate_str)
            
            video_kbps = parse_bitrate(video_bitrate)
            audio_kbps = parse_bitrate(audio_bitrate)
            
            # Total bitrate in kbps
            total_kbps = video_kbps + audio_kbps
            
            # File size = (bitrate in kbps * duration in seconds) / 8 (to convert to KB)
            # Then * 1024 to convert to bytes
            estimated_bytes = (total_kbps * duration * 1024) / 8
            
            # Add 10% overhead for container/metadata
            estimated_bytes = estimated_bytes * 1.1
            
            return int(estimated_bytes)
            
        except Exception as e:
            self.ui.logger.error(f"Error estimating file size: {e}")
            # Fallback: assume 500MB
            return 500 * 1024 * 1024

    def start_video_transcode(self, mkv_path, video_index=0, audio_index=None, user_agent=None):
        """Start video transcode/copy job and return immediate response"""
        # Route Chrome to WebM transcoder
        if self._is_chrome_browser(user_agent):
            self.ui.logger.info("Chrome detected, using WebM transcoder")
            return self.webm_transcoder.start_transcode(mkv_path, video_index, audio_index)

        # Firefox and others - use existing MP4 code
        self.ui.logger.info("Non-Chrome browser, using MP4 transcoder")

        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}

        duration = self._get_video_duration(mkv_path)
        
        needs_transcode = True
        # Generate cache filename - NO operation parameter
        cache_key = self._generate_cache_key(video_index, audio_index)
        cache_filename = self._get_cache_filename(mkv_path, 'video', cache_key, 'transcode')
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # Check if already processed
        if os.path.exists(cache_path):
            file_size = os.path.getsize(cache_path)
            if file_size > 1024:  # More than 1KB, likely valid
                return {
                    'success': True,
                    'url': f'/cache/{cache_filename}',
                    'status': 'completed',
                    'progress': 100,
                    'size': file_size,
                    'duration': duration
                }

        # Estimate final file size based on encoding settings
        is_rpi = self._is_raspberry_pi()
        video_bitrate = '1500k' if is_rpi else '5000k'
        audio_bitrate = '128k' if is_rpi else '192k'
        estimated_size = self._estimate_transcoded_file_size(duration, video_bitrate, audio_bitrate)
        self.estimated_file_size[cache_filename] = estimated_size
        
        # Simple job_key - just path and cache_key
        job_key = f"{mkv_path}_{cache_key}"
        
        # Check if processing is in progress
        if job_key in self.transcode_jobs and self.transcode_jobs[job_key]['status'] in ['processing', 'completed', 'starting']:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...'),
                'duration': duration,
                'estimated_size': estimated_size
            }
        
        # Start new job in background
        self.transcode_jobs[job_key] = {
            'status': 'starting',
            'progress': 0,
            'output_path': cache_path,
            'started_at': time.time(),
            'needs_transcode': needs_transcode,
            'cached_path': self.get_cached_filename(f'{cache_filename}')
        }

        thread = threading.Thread(
            target=self._transcode_video_worker,
            args=(mkv_path, video_index, audio_index, cache_path, job_key, needs_transcode)
        )
        thread.daemon = True
        thread.start()
        
        action = 'Transcoding' if needs_transcode else 'Copying'
        return {
            'success': True,
            'url': f'/cache/{cache_filename}',
            'status': 'processing',
            'progress': 0,
            'message': f'{action} started in background',
            'duration': duration,
            'estimated_size': estimated_size
        }

    def _parse_ffmpeg_progress(self, process, job_key, duration):
        """Parse FFmpeg progress output and update job status"""
        try:
            for line in process.stdout:
                # Check if job was cancelled
                if job_key in self.transcode_jobs and self.transcode_jobs[job_key].get('status') == 'cancelled':
                    self.ui.logger.info(f"Job {job_key} was cancelled, stopping...")
                    return False
                
                # Parse progress line: out_time_ms=12345678
                if line.startswith('out_time_ms='):
                    try:
                        time_ms = int(line.split('=')[1])
                        time_seconds = time_ms / 1000000.0  # Convert to seconds
                        
                        if duration > 0:
                            progress = min(int((time_seconds / duration) * 100), 99)
                            remaining = duration - time_seconds
                            
                            if remaining > 0:
                                eta = f"{int(remaining)}s remaining"
                            else:
                                eta = "almost done..."
                            
                            if job_key in self.transcode_jobs:
                                self.transcode_jobs[job_key].update({
                                    'progress': progress,
                                    'eta': eta,
                                    'current_time': time_seconds
                                })
                            
                            # Log progress every 10%
                            if progress % 10 == 0 and progress > 0:
                                self.ui.logger.info(f"Progress: {progress}% - {eta}")
                    except (ValueError, IndexError):
                        pass  # Skip malformed lines
            
            completed_cached_file = self.transcode_jobs[job_key]['cached_path']

            self.ui.logger.info(f"cachhed_file: {completed_cached_file}")
            if os.path.isfile(completed_cached_file):
                trigger_file = completed_cached_file  + '.finished'
                open(trigger_file, 'w').close()
                self.ui.logger.info(f"trigger_file: {trigger_file}")
            return True  # Completed normally
        except Exception as e:
            self.ui.logger.error(f"Error parsing FFmpeg progress: {e}")
            return False

    def _build_audio_encoding_args(self, mkv_path, audio_index):
        """Build FFmpeg arguments for audio encoding - copy if supported, transcode if not"""
        if audio_index is None:
            return []

        return [
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000'
        ]

    def get_transcode_status(self, mkv_path, video_index=0, audio_index=None, user_agent=None):
        """Get status of ongoing transcode"""
        # Route Chrome to WebM status
        if self._is_chrome_browser(user_agent):
            return self.webm_transcoder.get_status(mkv_path, video_index, audio_index)

        cache_key = self._generate_cache_key(video_index, audio_index)
        cache_filename = self._get_cache_filename(mkv_path, 'video', cache_key, 'transcode')
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        job_key = f"{mkv_path}_{cache_key}"
        
        # Check if actively processing
        if job_key in self.transcode_jobs:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...'),
                'current_time': job.get('current_time', 0)
            }
        
        # Check if completed
        if job_key in self.transcode_status:
            status = self.transcode_status[job_key]
            
            if status == 'completed' and os.path.exists(cache_path):
                file_size = os.path.getsize(cache_path)
                return {
                    'success': True,
                    'url': f'/cache/{cache_filename}',
                    'status': 'completed',
                    'progress': 100,
                    'size': file_size
                }
            elif status == 'failed':
                return {
                    'success': True,
                    'url': f'/cache/{cache_filename}',
                    'status': 'failed',
                    'progress': 0,
                    'error': 'Process failed'
                }
        
        return {
            'success': False,
            'status': 'not_found',
            'message': 'No job found'
        }

    def cancel_video_transcode(self, mkv_path, video_index=0, audio_index=None, user_agent=None):
        """Cancel ongoing transcode job"""
        # Route Chrome to WebM status
        if self._is_chrome_browser(user_agent):
            return self.webm_transcoder.cancel_transcode(mkv_path, video_index, audio_index)

        cache_key = self._generate_cache_key(video_index, audio_index)
        job_key = f"{mkv_path}_{cache_key}"
        
        if job_key not in self.transcode_jobs:
            return {
                'success': False,
                'error': 'No transcode job found'
            }
        
        job = self.transcode_jobs[job_key]
        
        # Kill the FFmpeg process if it exists
        if 'process' in job:
            try:
                process = job['process']
                process.terminate()  # Try graceful termination
                
                # Wait up to 3 seconds for process to terminate
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()  # Force kill if needed
                    process.wait()
                
                self.ui.logger.info(f"Transcode job {job_key} terminated")
            except Exception as e:
                self.ui.logger.error(f"Error killing transcode process: {e}")
        
        # Clean up partial output file
        output_path = job.get('output_path')
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
                self.ui.logger.info(f"Removed partial transcode file: {output_path}")
            except Exception as e:
                self.ui.logger.error(f"Error removing partial file: {e}")
        
        # Update job status
        job.update({
            'status': 'cancelled',
            'progress': 0
        })
        
        # Remove from active jobs after a delay
        def cleanup_job():
            time.sleep(5)
            if job_key in self.transcode_jobs:
                del self.transcode_jobs[job_key]
        
        cleanup_thread = threading.Thread(target=cleanup_job)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        return {
            'success': True,
            'message': 'Transcode job cancelled',
            'status': 'cancelled'
        }

    def _get_source_video_codec(self, mkv_path, video_index):
        """Get the codec of the source video stream"""
        try:
            info = self.get_mkv_info(mkv_path)
            if info and info.get('video'):
                for vid in info['video']:
                    if vid['index'] == video_index:
                        codec = vid.get('codec', '')
                        self.ui.logger.info(f"Source video codec: {codec}")
                        return codec
            
            self.ui.logger.warning(f"Could not detect video codec for index {video_index}")
            return None
            
        except Exception as e:
            self.ui.logger.error(f"Error getting source codec: {e}")
            return None

    def _build_video_encoding_args(self, needs_transcode, source_codec=None, mkv_path=None, video_index=0):
        """Build FFmpeg arguments for video encoding"""
        
        if not needs_transcode:
            self.ui.logger.info("Copying video stream (compatible codec)")
            return ['-c:v', 'copy']
        
        self.ui.logger.info("Transcoding video stream...")
        
        settings = self._get_optimal_transcode_settings(source_codec)
        args = []

        # Build filter arguments
        if 'scale' in settings and settings['scale']:
            args.extend(['-vf', f'scale={settings["scale"]}'])
        
        # Encoding settings
        if settings.get('use_hw'):
            args.extend([
                '-c:v', settings.get('encoder', 'h264_v4l2m2m'),
                '-b:v', settings.get('bitrate', '1500k'),
                '-num_output_buffers', '16',
                '-num_capture_buffers', '8',
            ])
            self.ui.logger.info("HW encoding 480p")
        else:
            args.extend([
                '-c:v', settings.get('encoder', 'libx264'),
                '-preset', settings.get('preset', 'ultrafast'),
                '-crf', settings.get('crf', '28'),
                '-threads', settings.get('threads', '4'),
                '-profile:v', settings.get('profile', 'baseline'),
                '-level', settings.get('level', '3.1'),
                '-pix_fmt', settings.get('pix_fmt', 'yuv420p')
            ])
            self.ui.logger.info("SW encoding 480p")
        
        return args

    def _transcode_video_worker(self, mkv_path, video_index, audio_index, output_path, job_key, needs_transcode=True):
        """Background worker for video transcoding/copying with progress tracking"""
        process = None
        try:
            # Get video duration for progress calculation
            duration = self._get_video_duration(mkv_path)
            source_codec = self._get_source_video_codec(mkv_path, video_index)

            # If audio_index not provided, auto-detect first audio track
            if audio_index is None:
                info = self.get_mkv_info(mkv_path)
                if info and info.get('audio') and len(info['audio']) > 0:
                    audio_index = info['audio'][0]['index']
                    self.ui.logger.info(f"Auto-detected audio track: {audio_index}")
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', mkv_path
            ]
            
            # Map video and audio streams
            if audio_index is not None:
                cmd.extend(['-map', f'0:{video_index}', '-map', f'0:{audio_index}'])
            else:
                cmd.extend(['-map', f'0:{video_index}'])
            
            video_args = self._build_video_encoding_args(needs_transcode, source_codec, mkv_path, video_index)
            cmd.extend(video_args)

            # Audio encoding settings - CONDITIONAL
            audio_args = self._build_audio_encoding_args(mkv_path, audio_index)
            cmd.extend(audio_args)
            
            # Output settings for streaming
            cmd.extend([
                '-movflags', '+frag_keyframe+empty_moov+default_base_moof',  # Enable progressive streaming
                '-flush_packets', '1',
                '-frag_duration', '1000000',
                '-min_frag_duration', '1000000',
                '-f', 'mp4',                # Force MP4 format
                '-progress', 'pipe:1',       # Output progress to stdout
                '-y',                        # Overwrite output
                output_path
            ])
            
            action = "transcode" if needs_transcode else "copy"
            self.ui.logger.info(f"Starting {action}: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
                bufsize=1
            )
            
            # Store process in job for cancellation
            self.transcode_jobs[job_key]['process'] = process
            self.transcode_jobs[job_key]['status'] = 'processing'
            
            # Parse FFmpeg progress output
            progress_completed = self._parse_ffmpeg_progress(process, job_key, duration)
            
            # Wait for process to complete
            process.wait()
            
            # Check if cancelled during processing
            if not progress_completed or self.transcode_jobs[job_key].get('status') == 'cancelled':
                return
            
            # Check result
            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.transcode_jobs[job_key].update({
                    'status': 'completed',
                    'progress': 100,
                    'size': file_size
                })
                self.ui.logger.info(f"Job completed: {output_path} ({file_size} bytes)")
            else:
                # Read stderr for error info
                stderr = process.stderr.read() if process.stderr else ''
                self.transcode_jobs[job_key].update({
                    'status': 'failed',
                    'error': f'FFmpeg failed with code {process.returncode}'
                })
                self.ui.logger.info(f"Job failed for {mkv_path}: {stderr}")
                
        except Exception as e:
            self.ui.logger.error(f"Error in worker: {e}")
            import traceback
            traceback.print_exc()
            self.transcode_jobs[job_key].update({
                'status': 'failed',
                'error': str(e)
            })
        finally:
            # Clean up process reference
            if job_key in self.transcode_jobs and 'process' in self.transcode_jobs[job_key]:
                del self.transcode_jobs[job_key]['process']
    
    def _get_video_duration(self, mkv_path):
        """Get video duration in seconds"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                mkv_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            self.ui.logger.error(f"Error getting video duration: {e}")
            return 0
    
    def _get_cache_filename(self, mkv_path, track_type, track_index, operation):
        """Generate cache filename"""
        hash_input = f"{mkv_path}_{track_type}_{track_index}_{operation}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        # For audio, determine extension based on codec and browser support
        if track_type == 'audio':
            info = self.get_mkv_info(mkv_path)
            if info and info.get('audio'):
                for aud in info['audio']:
                    if aud['index'] == track_index:
                        codec = aud.get('codec', '').lower()
                        
                        # If browser-playable, use native extension
                        if self._is_audio_browser_playable(codec):
                            codec_extensions = {
                                'aac': '.m4a',
                                'mp3': '.mp3',
                                'opus': '.opus',
                                'vorbis': '.ogg',
                                'flac': '.flac'
                            }
                            ext = codec_extensions.get(codec, '.m4a')
                        else:
                            # Will be transcoded to AAC
                            ext = '.m4a'
                        
                        return f"{file_hash}_{track_type}_{track_index}{ext}"
            
            # Fallback - assume AAC transcode
            return f"{file_hash}_{track_type}_{track_index}.m4a"
        
        # Default extensions for other track types
        extensions = {
            'subtitle_extract': '.vtt',
            'video_transcode': '.mp4'
        }
        ext = extensions.get(f"{track_type}_{operation}", '.dat')
        
        return f"{file_hash}_{track_type}_{track_index}{ext}"
   
    # ===========================
    # TRACK INFO
    # ===========================
    
    def get_mkv_info(self, mkv_path):
        """Extract track information from MKV file using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                mkv_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            tracks = {
                'video': [],
                'audio': [],
                'subtitle': []
            }
            
            for stream in data.get('streams', []):
                codec_type = stream.get('codec_type')
                if codec_type in tracks:
                    track_info = {
                        'index': stream.get('index'),
                        'codec': stream.get('codec_name'),
                        'language': stream.get('tags', {}).get('language', 'und'),
                        'title': stream.get('tags', {}).get('title', ''),
                    }
                    
                    if codec_type == 'audio':
                        track_info.update({
                            'channels': stream.get('channels'),
                            'sample_rate': stream.get('sample_rate')
                        })
                    
                    tracks[codec_type].append(track_info)
            
            return tracks
        except Exception as e:
            self.ui.logger.error(f"Error getting MKV info: {e}")
            return None
    
    # ===========================
    # SUBTITLE OPERATIONS
    # ===========================

    def _get_external_subtitles(self, mkv_path):
        """Find external subtitle files in the same directory"""
        try:
            video_dir = os.path.dirname(mkv_path)
            video_name = os.path.splitext(os.path.basename(mkv_path))[0]
            
            # Supported subtitle extensions
            sub_extensions = ['.srt', '.vtt', '.ass', '.ssa']
            
            external_subs = []
            
            # Look for files matching video name
            for file in os.listdir(video_dir):
                file_lower = file.lower()
                
                # Check if file starts with video name and has subtitle extension
                for ext in sub_extensions:
                    if file_lower.startswith(video_name.lower()) and file_lower.endswith(ext):
                        sub_path = os.path.join(video_dir, file)
                        
                        # Try to detect language from filename (e.g., video.en.srt, video.eng.srt)
                        language = 'und'
                        name_parts = os.path.splitext(file)[0].split('.')
                        if len(name_parts) > 1:
                            lang_code = name_parts[-1].lower()
                            if len(lang_code) in [2, 3]:  # ISO language codes
                                language = lang_code
                        
                        external_subs.append({
                            'path': sub_path,
                            'language': language,
                            'title': file,
                            'codec': ext[1:]  # Remove dot from extension
                        })
            
            if external_subs:
                self.ui.logger.info(f"Found {len(external_subs)} external subtitle file(s)")
            
            return external_subs
            
        except Exception as e:
            self.ui.logger.error(f"Error finding external subtitles: {e}")
            return []
    
    
    def get_all_subtitles(self, mkv_path):
        """Extract all subtitle tracks and return content (including external files)"""
        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}
        
        results = []
        
        # Get external subtitle files from same directory
        external_subs = self._get_external_subtitles(mkv_path)
        for ext_sub in external_subs:
            try:
                with open(ext_sub['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                results.append({
                    'index': f"ext_{len(results)}",
                    'language': ext_sub['language'],
                    'title': ext_sub['title'],
                    'codec': ext_sub['codec'],
                    'content': content,
                    'external': True
                })
            except Exception as e:
                self.ui.logger.error(f"Failed to read external subtitle {ext_sub['path']}: {e}")
        
        # Get embedded subtitles
        info = self.get_mkv_info(mkv_path)
        self.ui.logger.info(info)
        
        if info and info.get('subtitle'):
            unsupported_count = 0
            
            for subtitle in info['subtitle']:
                self.ui.logger.info(subtitle)
                track_index = subtitle['index']
                codec = subtitle.get('codec', '').lower()
                
                # Skip bitmap subtitles
                if codec in ['dvd_subtitle', 'dvdsub', 'hdmv_pgs_subtitle', 'pgssub', 'vobsub']:
                    unsupported_count += 1
                    self.ui.logger.info(f"Skipping bitmap subtitle track {track_index} ({codec})")
                    continue
                
                cache_filename = self._get_cache_filename(mkv_path, 'subtitle', track_index, 'extract')
                cache_path = os.path.join(self.cache_dir, cache_filename)
                
                if not os.path.exists(cache_path):
                    self.ui.logger.info(f"Extracting subtitle track {track_index}...")
                    if not self._extract_subtitle(mkv_path, track_index, cache_path):
                        continue
                
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        vtt_content = f.read()
                    
                    results.append({
                        'index': track_index,
                        'language': subtitle['language'],
                        'title': subtitle['title'],
                        'codec': subtitle['codec'],
                        'content': vtt_content,
                        'external': False
                    })
                except Exception as e:
                    self.ui.logger.error(f"Failed to read subtitle: {e}")
        
        return {'success': True, 'tracks': results}
    
    def _extract_subtitle(self, mkv_path, track_index, output_path):
        """Extract and convert subtitle to WebVTT"""
        try:
            cmd = [
                'ffmpeg',
                '-i', mkv_path,
                '-map', f'0:{track_index}',
                '-c:s', 'webvtt',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.ui.logger.info("Direct VTT conversion failed, trying alternative...")
                temp_srt = output_path.replace('.vtt', '.temp.srt')
                
                cmd = ['ffmpeg', '-i', mkv_path, '-map', f'0:{track_index}', '-y', temp_srt]
                subprocess.run(cmd, capture_output=True, check=True)
                
                cmd = ['ffmpeg', '-i', temp_srt, '-c:s', 'webvtt', '-y', output_path]
                subprocess.run(cmd, capture_output=True, check=True)
                
                if os.path.exists(temp_srt):
                    os.remove(temp_srt)
            
            return os.path.exists(output_path)
        except Exception as e:
            self.ui.logger.error(f"Error extracting subtitle: {e}")
            return False
    
    # ===========================
    # AUDIO OPERATIONS
    # ===========================
    def get_all_audio_tracks(self, mkv_path):
        """Get all audio tracks - start async extraction"""
        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}
        
        info = self.get_mkv_info(mkv_path)
        if not info or not info.get('audio'):
            return {'success': True, 'tracks': []}
        
        results = []
        for audio in info['audio']:
            track_index = audio['index']
            
            # Start async extraction
            extraction_result = self.start_audio_extraction(mkv_path, track_index)
            
            results.append({
                'index': track_index,
                'language': audio['language'],
                'title': audio['title'],
                'codec': audio['codec'],
                'channels': audio['channels'],
                'sample_rate': audio['sample_rate'],
                'url': extraction_result.get('url', ''),
                'status': extraction_result.get('status', 'pending'),
                'progress': extraction_result.get('progress', 0)
            })

        return {'success': True, 'tracks': results}
    
    def _is_browser_compatible_audio(self, codec):
        """Check if audio codec is browser-compatible"""
        compatible_codecs = ['aac', 'mp3', 'opus', 'vorbis', 'flac', 'pcm_s16le', 'pcm_s24le']
        return codec.lower() in compatible_codecs
    
    def _extract_audio(self, mkv_path, track_index, output_path, transcode=False):
        """Extract audio track (auto-transcode if incompatible)"""
        try:
            if not transcode:
                cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-select_streams', f'{track_index}',
                    '-show_entries', 'stream=codec_name',
                    '-of', 'json',
                    mkv_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                probe_data = json.loads(result.stdout)
                
                if probe_data.get('streams'):
                    codec = probe_data['streams'][0].get('codec_name', '')
                    if not self._is_browser_compatible_audio(codec):
                        self.ui.logger.info(f"Codec '{codec}' not browser-compatible, transcoding...")
                        transcode = True
            
            if transcode:
                cmd = [
                    'ffmpeg',
                    '-i', mkv_path,
                    '-movflags', '+faststart+empty_moov',  # Enable progressive streaming
                    '-flush_packets', '1',
                    '-progress', 'pipe:1',       # Output progress to stdout
                    '-map', f'0:{track_index}',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-ar', '48000',
                    '-y',
                    output_path
                ]
            else:
                cmd = [
                    'ffmpeg',
                    '-i', mkv_path,
                    '-progress', 'pipe:1',       # Output progress to stdout
                    '-map', f'0:{track_index}',
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]

            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            self.ui.logger.error(f"Error extracting audio: {e}")
            if not transcode:
                return self._extract_audio(mkv_path, track_index, output_path, transcode=True)
            return False
    
    # ===========================
    # CACHE OPERATIONS
    # ===========================

    def get_cached_filename(self, cache_filename):
        return os.path.join(self.cache_dir, cache_filename)

    def get_cached_file(self, cache_filename):
        """Retrieve cached file info for streaming"""
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        content_type, _ = mimetypes.guess_type(cache_path)
        if not content_type:
            content_type = 'application/octet-stream'

        file_size = os.path.getsize(cache_path) if os.path.isfile(cache_path) else 1024*1024

        # Always return file path for streaming (not data)
        return {
            'file_path': cache_path,
            'content_type': content_type,
            'file_size': file_size
        }

    def handle_subtitle_request(self, series_id, request_body):
        """Handle POST /series/:id/subtitle"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            
            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 404
            
            result = self.get_all_subtitles(mkv_path)
            return result, 200
            
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 500
        except Exception as e:
            self.ui.logger.info(f"Error handling subtitle request: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    def handle_audio_request(self, series_id, request_body):
        """Handle POST /series/:id/audio"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            
            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 404
            
            result = self.get_all_audio_tracks(mkv_path)
            return result, 200
            
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 500
        except Exception as e:
            self.ui.logger.info(f"Error handling audio request: {e}")
            return {'success': False, 'error': str(e)}, 500

    # ===========================
    # VIDEO TRANSCODE HANDLERS
    # ===========================

    def handle_transcode_request(self, series_id, request_body, user_agent):
        """Handle POST /series/:id/transcode - Start transcode job"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            video_index = data.get('video_index', 0)
            audio_index = data.get('audio_index')  # Optional

            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 400

            result = self.start_video_transcode(mkv_path, video_index, audio_index, user_agent)
            return result, 200

        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 400
        except Exception as e:
            self.ui.logger.error(f"Error handling transcode request: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}, 500
  
    def handle_transcode_status_request(self, series_id, request_body, user_agent):
        """Handle POST /series/:id/transcode/status - Get transcode/extraction progress"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            video_index = data.get('video_index')
            audio_index = data.get('audio_index')
            track_type = data.get('track_type', 'video')  # 'video' or 'audio'

            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 400
            
            if track_type == 'audio' and audio_index is not None:
                # Audio extraction status
                result = self.get_audio_extraction_status(mkv_path, audio_index)
            else:
                # Video transcode status
                result = self.get_transcode_status(mkv_path, video_index or 0, audio_index, user_agent)
            
            return result, 200
     
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 400
        except Exception as e:
            self.ui.logger.error(f"Error handling transcode status request: {e}")
            return {'success': False, 'error': str(e)}, 500

    def handle_transcode_cancel_request(self, series_id, request_body, user_agent):
        """Handle POST /series/:id/transcode/cancel - Cancel transcode job"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            video_index = data.get('video_index', 0)
            audio_index = data.get('audio_index')  # Optional
            
            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 400
            
            result = self.cancel_video_transcode(mkv_path, video_index, audio_index, user_agent)
            return result, 200

        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 400
        except Exception as e:
            self.ui.logger.error(f"Error handling transcode cancel request: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    def handle_cache_request(self, cache_filename):
        """Handle GET /cache/{filename} - Returns file data or path"""
        if cache_filename.endswith('.webm'):
            return self.webm_transcoder.get_cached_file(cache_filename)
        return self.get_cached_file(cache_filename)
