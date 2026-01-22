import subprocess
import os
import hashlib
import threading
import time

class WebMTranscoder:
    """Separate transcoder for WebM/VP8 - optimized for Chrome and Raspberry Pi"""
    
    def __init__(self, ui):
        self.ui = ui
        self.cache_dir = os.path.join(ui.home_folder, "tmp")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.transcode_jobs = {}
        self.estimated_file_size = {}
    
    def _is_raspberry_pi(self):
        """Check if running on Raspberry Pi"""
        try:
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
            return 'rpt-rpi' in result.stdout or 'raspi' in result.stdout
        except:
            return False
    
    def _get_vp8_settings(self):
        """Get optimized VP8 settings - similar to ultrafast for H.264"""
        if self._is_raspberry_pi():
            return {
                'speed': '8',  # Fastest speed (0-8, higher is faster)
                'cpu_used': '8',  # Maximum speed preset
                'bitrate': '1500k',  # Lower bitrate for faster encoding
                'audio_bitrate': '96k',
                'threads': '4',
                'deadline': 'realtime',  # Realtime mode (like ultrafast)
                'crf': '28',  # Higher CRF = lower quality but faster (similar to crf 28)
                'scale': '-2:480'  # Scale to 480p like H.264 version
            }
        else:
            return {
                'speed': '4',
                'cpu_used': '4',
                'bitrate': '2500k',
                'audio_bitrate': '128k',
                'threads': '0',
                'deadline': 'good',
                'crf': '23',
                'scale': '-2:720'  # Higher resolution for non-RPi
            }
    
    def _generate_cache_key(self, video_path, video_index, audio_index):
        """Generate cache filename for WebM"""
        hash_input = f"{video_path}_webm_{video_index}_{audio_index}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"{file_hash}_webm.webm"
    
    def _get_video_duration(self, video_path):
        """Get video duration"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0
    
    def _estimate_file_size(self, duration, bitrate='1500k'):
        """Estimate WebM file size"""
        try:
            if 'M' in bitrate:
                bitrate_kbps = float(bitrate.replace('M', '')) * 1000
            elif 'k' in bitrate:
                bitrate_kbps = float(bitrate.replace('k', ''))
            else:
                bitrate_kbps = float(bitrate)
            
            # Add audio bitrate (96k for RPi, 128k for desktop)
            total_kbps = bitrate_kbps + 96
            
            # File size in bytes
            estimated_bytes = (total_kbps * duration * 1024) / 8
            
            # Add 10% overhead
            return int(estimated_bytes * 1.1)
        except:
            return 500 * 1024 * 1024
    
    def start_transcode(self, video_path, video_index=0, audio_index=None):
        """Start WebM transcode"""
        if not os.path.exists(video_path):
            return {'success': False, 'error': 'File not found'}
        
        cache_filename = self._generate_cache_key(video_path, video_index, audio_index)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # Check if already exists
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
        
        job_key = f"{video_path}_webm_{video_index}_{audio_index}"
        
        # Check if already processing
        if job_key in self.transcode_jobs and self.transcode_jobs[job_key]['status'] in ['processing', 'completed', 'starting']:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...')
            }
        
        duration = self._get_video_duration(video_path)
        settings = self._get_vp8_settings()
        estimated_size = self._estimate_file_size(duration, settings['bitrate'])
        self.estimated_file_size[cache_filename] = estimated_size
        
        # Create job
        self.transcode_jobs[job_key] = {
            'status': 'starting',
            'progress': 0,
            'output_path': cache_path,
            'started_at': time.time(),
            'cached_path': cache_path
        }
        
        # Start worker thread
        thread = threading.Thread(
            target=self._transcode_worker,
            args=(video_path, video_index, audio_index, cache_path, job_key, duration)
        )
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'url': f'/cache/{cache_filename}',
            'status': 'processing',
            'progress': 0,
            'message': 'WebM transcoding started',
            'estimated_size': estimated_size
        }
    
    def _transcode_worker(self, video_path, video_index, audio_index, output_path, job_key, duration):
        """Background worker for WebM transcoding - optimized like H.264 ultrafast"""
        process = None
        try:
            settings = self._get_vp8_settings()
            # If audio_index not provided, auto-detect first audio track
            if audio_index is None:
                info = self.ui.track_extractor.get_mkv_info(video_path)
                if info and info.get('audio') and len(info['audio']) > 0:
                    audio_index = info['audio'][0]['index']
                    self.ui.logger.info(f"Auto-detected audio track: {audio_index}")
            
            # Build FFmpeg command - similar structure to H.264 version
            cmd = [
                'ffmpeg',
                '-i', video_path
            ]
            
            # Map streams
            if audio_index is not None:
                cmd.extend(['-map', f'0:{video_index}', '-map', f'0:{audio_index}'])
            else:
                cmd.extend(['-map', f'0:{video_index}'])
            
            # Add scaling filter (like -vf scale=-2:480)
            cmd.extend(['-vf', f"scale={settings['scale']}"])
            
            # VP8 video encoding - optimized for speed
            cmd.extend([
                '-c:v', 'libvpx',
                '-speed', settings['speed'],  # Maximum speed
                '-quality', settings['deadline'],  # realtime for RPi, good for desktop
                '-cpu-used', settings['cpu_used'],  # Maximum cpu-used
                '-deadline', settings['deadline'],
                '-threads', settings['threads'],
                '-b:v', settings['bitrate'],
                '-crf', settings['crf'],
                # Simplified settings for speed (removed complex features)
                '-auto-alt-ref', '0',  # Disable for speed
                '-lag-in-frames', '0',  # Disable for speed (like ultrafast)
                '-error-resilient', '1'  # Better for streaming
            ])
            
            # Opus audio encoding with sample rate
            if audio_index is not None:
                cmd.extend([
                    '-c:a', 'libopus',
                    '-b:a', settings['audio_bitrate'],
                    '-ar', '48000'  # Like H.264 version
                ])
            
            # WebM output with fragmentation (like movflags in H.264)
            cmd.extend([
                '-f', 'webm',
                '-live', '1',  # Enable live streaming mode
                '-chunk_start_index', '0',
                '-chunk_duration', '1000',  # 1 second chunks (like frag_duration)
                '-flush_packets', '1',  # Like H.264 version
                '-progress', 'pipe:1',
                '-y',
                output_path
            ])
            
            self.ui.logger.info(f"Starting WebM transcode: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
                bufsize=1
            )
            
            self.transcode_jobs[job_key]['process'] = process
            self.transcode_jobs[job_key]['status'] = 'processing'
            
            # Parse progress
            self._parse_progress(process, job_key, duration)
            
            process.wait()
            
            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.transcode_jobs[job_key].update({
                    'status': 'completed',
                    'progress': 100,
                    'size': file_size
                })
                
                # Create finished trigger
                trigger_file = output_path + '.finished'
                open(trigger_file, 'w').close()
                
                self.ui.logger.info(f"WebM transcode completed: {output_path}")
            else:
                self.transcode_jobs[job_key].update({
                    'status': 'failed',
                    'error': f'FFmpeg failed with code {process.returncode}'
                })
        
        except Exception as e:
            self.ui.logger.error(f"WebM transcode error: {e}")
            self.transcode_jobs[job_key].update({
                'status': 'failed',
                'error': str(e)
            })
        finally:
            if job_key in self.transcode_jobs and 'process' in self.transcode_jobs[job_key]:
                del self.transcode_jobs[job_key]['process']
    
    def _parse_progress(self, process, job_key, duration):
        """Parse FFmpeg progress"""
        try:
            for line in process.stdout:
                if job_key in self.transcode_jobs and self.transcode_jobs[job_key].get('status') == 'cancelled':
                    return False
                
                if line.startswith('out_time_ms='):
                    try:
                        time_ms = int(line.split('=')[1])
                        time_seconds = time_ms / 1000000.0
                        
                        if duration > 0:
                            progress = min(int((time_seconds / duration) * 100), 99)
                            remaining = duration - time_seconds
                            eta = f"{int(remaining)}s remaining" if remaining > 0 else "almost done..."
                            
                            if job_key in self.transcode_jobs:
                                self.transcode_jobs[job_key].update({
                                    'progress': progress,
                                    'eta': eta
                                })
                    except:
                        pass
            return True
        except:
            return False
    
    def get_status(self, video_path, video_index=0, audio_index=None):
        """Get transcode status"""
        cache_filename = self._generate_cache_key(video_path, video_index, audio_index)
        cache_path = os.path.join(self.cache_dir, cache_filename)
        job_key = f"{video_path}_webm_{video_index}_{audio_index}"
        
        if job_key in self.transcode_jobs:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...')
            }
        
        if os.path.exists(cache_path):
            file_size = os.path.getsize(cache_path)
            return {
                'success': True,
                'url': f'/cache/{cache_filename}',
                'status': 'completed',
                'progress': 100,
                'size': file_size
            }
        
        return {'success': False, 'status': 'not_found'}
    
    def cancel_transcode(self, video_path, video_index=0, audio_index=None):
        """Cancel transcode"""
        job_key = f"{video_path}_webm_{video_index}_{audio_index}"
        
        if job_key not in self.transcode_jobs:
            return {'success': False, 'error': 'No job found'}
        
        job = self.transcode_jobs[job_key]
        
        if 'process' in job:
            try:
                process = job['process']
                process.terminate()
                try:
                    process.wait(timeout=3)
                except:
                    process.kill()
                    process.wait()
            except:
                pass
        
        output_path = job.get('output_path')
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        
        job.update({'status': 'cancelled', 'progress': 0})
        
        return {'success': True, 'message': 'WebM transcode cancelled'}
    
    def get_cached_file(self, cache_filename):
        """Get cached WebM file info"""
        cache_path = os.path.join(self.cache_dir, cache_filename)
        file_size = os.path.getsize(cache_path) if os.path.isfile(cache_path) else 1024*1024
        
        return {
            'file_path': cache_path,
            'content_type': 'video/webm',
            'file_size': file_size
        }
