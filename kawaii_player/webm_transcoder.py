import subprocess
import os
import hashlib
import threading
import time

class WebMTranscoder:
    """Separate transcoder for WebM/VP8 - optimized for Chrome"""
    
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
        """Get optimized VP8 settings"""
        if self._is_raspberry_pi():
            return {
                'speed': '8',
                'cpu_used': '8',
                'bitrate': '1M',
                'audio_bitrate': '96k',
                'threads': '4'
            }
        else:
            return {
                'speed': '6',
                'cpu_used': '6',
                'bitrate': '2M',
                'audio_bitrate': '128k',
                'threads': '8'
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
    
    def _estimate_file_size(self, duration, bitrate='2M'):
        """Estimate WebM file size"""
        try:
            if 'M' in bitrate:
                bitrate_kbps = float(bitrate.replace('M', '')) * 1000
            elif 'k' in bitrate:
                bitrate_kbps = float(bitrate.replace('k', ''))
            else:
                bitrate_kbps = float(bitrate)
            
            # Add audio bitrate (128k)
            total_kbps = bitrate_kbps + 128
            
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
        #self._create_webm_header_with_duration(cache_path, duration)
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
        """Background worker for WebM transcoding"""
        process = None
        try:
            settings = self._get_vp8_settings()
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', video_path
            ]
            
            # Map streams
            if audio_index is not None:
                cmd.extend(['-map', f'0:{video_index}', '-map', f'0:{audio_index}'])
            else:
                cmd.extend(['-map', f'0:{video_index}'])
            
            # VP8 video encoding
            cmd.extend([
                '-c:v', 'libvpx',
                '-speed', settings['speed'],
                '-quality', 'realtime',
                '-cpu-used', settings['cpu_used'],
                '-deadline', 'realtime',
                '-threads', settings['threads'],
                '-b:v', settings['bitrate'],
                '-auto-alt-ref', '0',
                '-lag-in-frames', '0',
                '-crf', '10'
            ])
            
            # Opus audio encoding
            if audio_index is not None:
                cmd.extend([
                    '-c:a', 'libopus',
                    '-b:a', settings['audio_bitrate']
                ])
            
            # WebM output
            cmd.extend([
                '-f', 'webm',
                '-live', '1',
                '-chunk_start_index', '0',
                '-chunk_duration', '2000',
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

    def _create_webm_header_with_duration(self, output_path, duration):
        """Create initial WebM file with duration metadata"""
        try:
            # Create a minimal WebM file with just EBML header and duration
            import struct
            
            # This creates a valid WebM header that Chrome can parse
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'color=c=black:s=32x32:d=0.1',  # Tiny black frame
                '-c:v', 'libvpx',
                '-an',
                '-f', 'webm',
                '-metadata', f'duration={duration}',
                '-t', '0.1',
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=5)
            self.ui.logger.info(f"Created WebM header with duration: {duration}s")
            
        except Exception as e:
            self.ui.logger.error(f"Error creating WebM header: {e}")
    
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
