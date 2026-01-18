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

    # ===========================
    # VIDEO TRANSCODING
    # ===========================

    def _generate_cache_key(self, video_index, audio_index):
        """Generate consistent cache key"""
        if audio_index is not None:
            self.ui.logger.info(f"aid:{audio_index} selected")
        return str(video_index)
    
    
    def start_video_transcode(self, mkv_path, video_index=0, audio_index=None):
        """Start video transcode/copy job and return immediate response"""
        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}
        
        # Check if video needs transcoding
        info = self.get_mkv_info(mkv_path)
        needs_transcode = True
        
        if info and info.get('video'):
            video_track = None
            for vid in info['video']:
                if vid['index'] == video_index:
                    video_track = vid
                    break
            
            if video_track:
                video_codec = video_track.get('codec', '')
                needs_transcode = not self._is_browser_compatible_video(video_codec)
                self.ui.logger.info(f"Video codec: {video_codec}, needs_transcode: {needs_transcode}")
        
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
                    'size': file_size
                }
        
        # Simple job_key - just path and cache_key
        job_key = f"{mkv_path}_{cache_key}"
        
        # Check if processing is in progress
        if job_key in self.transcode_jobs:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...')
            }
        
        # Start new job in background
        self.transcode_jobs[job_key] = {
            'status': 'starting',
            'progress': 0,
            'output_path': cache_path,
            'started_at': time.time(),
            'needs_transcode': needs_transcode
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
            'message': f'{action} started in background'
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
            
            return True  # Completed normally
        except Exception as e:
            self.ui.logger.error(f"Error parsing FFmpeg progress: {e}")
            return False

    def _build_audio_encoding_args(self, mkv_path, audio_index):
        """Build FFmpeg arguments for audio encoding - copy if supported, transcode if not"""
        if audio_index is None:
            return []
        
        # Check if audio codec is browser-playable
        info = self.get_mkv_info(mkv_path)
        
        if info and info.get('audio'):
            for aud in info['audio']:
                if aud['index'] == audio_index:
                    audio_codec = aud.get('codec', '')
                    
                    if self._is_audio_browser_playable(audio_codec):
                        # Browser can play it - just copy
                        self.ui.logger.info(f"Copying audio stream {audio_index} ({audio_codec}) - browser playable")
                        return ['-c:a', 'copy']
                    else:
                        # Not browser-playable - transcode to AAC
                        self.ui.logger.info(f"Transcoding audio stream {audio_index} ({audio_codec}) to AAC - not browser playable")
                        return [
                            '-c:a', 'aac',
                            '-b:a', '192k',
                            '-ar', '48000'
                        ]
        
        # Fallback - transcode to AAC
        self.ui.logger.info(f"Transcoding audio stream {audio_index} to AAC (codec detection failed)")
        return [
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000'
        ]

    def get_transcode_status(self, mkv_path, video_index=0, audio_index=None):
        """Get status of ongoing transcode"""
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

    def cancel_video_transcode(self, mkv_path, video_index=0, audio_index=None):
        """Cancel ongoing transcode job"""
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

    def _transcode_video_worker(self, mkv_path, video_index, audio_index, output_path, job_key, needs_transcode=True):
        """Background worker for video transcoding/copying with progress tracking"""
        process = None
        try:
            # Get video duration for progress calculation
            duration = self._get_video_duration(mkv_path)

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
            
            # Video encoding settings - CONDITIONAL
            if needs_transcode:
                self.ui.logger.info(f"Transcoding video stream {video_index}...")
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',  # Fast encoding for real-time
                    '-crf', '23',           # Quality level (18-28 good range)
                    '-maxrate', '5M',       # Max bitrate
                    '-bufsize', '10M',      # Buffer size
                ])
            else:
                self.ui.logger.info(f"Copying video stream {video_index} (compatible codec)...")
                cmd.extend([
                    '-c:v', 'copy',  # Just copy, no re-encoding
                ])
            
            # Audio encoding settings - CONDITIONAL
            audio_args = self._build_audio_encoding_args(mkv_path, audio_index)
            cmd.extend(audio_args)
            
            # Output settings for streaming
            cmd.extend([
                '-movflags', '+faststart+empty_moov',  # Enable progressive streaming
                '-flush_packets', '1',
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
                stderr=subprocess.PIPE,
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
    
    def get_all_subtitles(self, mkv_path):
        """Extract all subtitle tracks and return content"""
        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}
        
        info = self.get_mkv_info(mkv_path)
        self.ui.logger.info(info)
        if not info or not info.get('subtitle'):
            return {'success': True, 'tracks': []}
        
        results = []
        for subtitle in info['subtitle']:
            self.ui.logger.info(subtitle)
            track_index = subtitle['index']
            
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
                    'content': vtt_content
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
        """Extract all audio tracks with auto-transcoding"""
        if not os.path.exists(mkv_path):
            return {'success': False, 'error': 'File not found'}
        
        info = self.get_mkv_info(mkv_path)
        self.ui.logger.info(info)
        if not info or not info.get('audio'):
            return {'success': True, 'tracks': []}
        
        results = []
        for audio in info['audio']:
            self.ui.logger.info(audio)
            track_index = audio['index']
            codec = audio['codec']
            
            needs_transcode = not self._is_browser_compatible_audio(codec)
            operation = 'transcode' if needs_transcode else 'extract'
            
            cache_filename = self._get_cache_filename(mkv_path, 'audio', track_index, operation)
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            if not os.path.exists(cache_path):
                self.ui.logger.info(f"Extracting audio track {track_index} (transcode={needs_transcode})...")
                self._extract_audio(mkv_path, track_index, cache_path, needs_transcode)
            
            results.append({
                'index': track_index,
                'language': audio['language'],
                'title': audio['title'],
                'codec': audio['codec'],
                'channels': audio['channels'],
                'sample_rate': audio['sample_rate'],
                'url': f'/cache/{cache_filename}',
                'transcoded': needs_transcode
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

    def get_cached_file(self, cache_filename):
        """Retrieve cached file info for streaming"""
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        content_type, _ = mimetypes.guess_type(cache_path)
        if not content_type:
            content_type = 'application/octet-stream'

        abs_file_path = self.cache_path_mapping.get(cache_filename)
        if abs_file_path and os.path.exists(abs_file_path):
            file_size_abs = os.path.getsize(abs_file_path)
        else:
            file_size_abs = os.path.getsize(cache_path)

        
        # Always return file path for streaming (not data)
        return {
            'file_path': cache_path,
            'content_type': content_type,
            'file_size': os.path.getsize(cache_path),
            'file_size_abs': file_size_abs
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

    def handle_transcode_request(self, series_id, request_body):
        """Handle POST /series/:id/transcode - Start transcode job"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            video_index = data.get('video_index', 0)
            audio_index = data.get('audio_index')  # Optional

            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 400

            result = self.start_video_transcode(mkv_path, video_index, audio_index)
            return result, 200

        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 400
        except Exception as e:
            self.ui.logger.error(f"Error handling transcode request: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}, 500
    
    def handle_transcode_status_request(self, series_id, request_body):
        """Handle POST /series/:id/transcode/status - Get transcode progress"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            video_index = data.get('video_index', 0)
            audio_index = data.get('audio_index')  # Optional

            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 400
            
            result = self.get_transcode_status(mkv_path, video_index, audio_index)
            return result, 200
 
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 400
        except Exception as e:
            self.ui.logger.error(f"Error handling transcode status request: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    def handle_transcode_cancel_request(self, series_id, request_body):
        """Handle POST /series/:id/transcode/cancel - Cancel transcode job"""
        try:
            data = json.loads(request_body)
            mkv_path = data.get('path')
            video_index = data.get('video_index', 0)
            audio_index = data.get('audio_index')  # Optional
            
            if not mkv_path:
                return {'success': False, 'error': 'Missing path parameter'}, 400
            
            result = self.cancel_video_transcode(mkv_path, video_index, audio_index)
            return result, 200

        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON'}, 400
        except Exception as e:
            self.ui.logger.error(f"Error handling transcode cancel request: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    def handle_cache_request(self, cache_filename):
        """Handle GET /cache/{filename} - Returns file data or path"""
        return self.get_cached_file(cache_filename)
