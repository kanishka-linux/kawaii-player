import subprocess
import os
import hashlib
import threading
import time

class HLSTranscoder:
    """HLS transcoder for iOS/Safari - generates m3u8 playlist + .ts segments"""
    
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
    
    def _get_h264_settings(self):
        """Get optimized H.264 settings for HLS"""
        if self._is_raspberry_pi():
            return {
                'preset': 'ultrafast',
                'crf': '28',
                'bitrate': '1500k',
                'audio_bitrate': '128k',
                'threads': '4',
                'scale': '-2:480',
                'profile': 'baseline',
                'level': '3.1'
            }
        else:
            return {
                'preset': 'faster',
                'crf': '23',
                'bitrate': '5000k',
                'audio_bitrate': '192k',
                'threads': '0',
                'scale': '-2:720',
                'profile': 'main',
                'level': '4.0'
            }
    
    def _generate_cache_key(self, video_path, video_index, audio_index):
        """Generate cache directory name for HLS"""
        hash_input = f"{video_path}_hls_{video_index}_{audio_index}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"{file_hash}_hls"
    
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
        """Estimate total HLS file size (all segments)"""
        try:
            if 'M' in bitrate:
                bitrate_kbps = float(bitrate.replace('M', '')) * 1000
            elif 'k' in bitrate:
                bitrate_kbps = float(bitrate.replace('k', ''))
            else:
                bitrate_kbps = float(bitrate)
            
            # Add audio bitrate
            total_kbps = bitrate_kbps + 128
            
            # File size in bytes
            estimated_bytes = (total_kbps * duration * 1024) / 8
            
            # Add 10% overhead
            return int(estimated_bytes * 1.1)
        except:
            return 500 * 1024 * 1024
    
    def start_transcode(self, video_path, video_index=0, audio_index=None):
        """Start HLS transcode"""
        if not os.path.exists(video_path):
            return {'success': False, 'error': 'File not found'}
        
        cache_dirname = self._generate_cache_key(video_path, video_index, audio_index)
        cache_dir_path = os.path.join(self.cache_dir, cache_dirname)
        
        # Create HLS directory
        os.makedirs(cache_dir_path, exist_ok=True)
        
        playlist_path = os.path.join(cache_dir_path, 'playlist.m3u8')
        
        # Check if already exists and completed
        if os.path.exists(playlist_path):
            finished_file = os.path.join(cache_dir_path, '.finished')
            if os.path.exists(finished_file):
                return {
                    'success': True,
                    'url': f'/cache/{cache_dirname}/playlist.m3u8',
                    'status': 'completed',
                    'progress': 100
                }
        
        job_key = f"{video_path}_hls_{video_index}_{audio_index}"
        
        # Check if already processing
        if job_key in self.transcode_jobs and self.transcode_jobs[job_key]['status'] in ['processing', 'completed', 'starting']:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_dirname}/playlist.m3u8',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...')
            }
        
        duration = self._get_video_duration(video_path)
        settings = self._get_h264_settings()
        estimated_size = self._estimate_file_size(duration, settings['bitrate'])
        self.estimated_file_size[cache_dirname] = estimated_size
        
        # Create job
        self.transcode_jobs[job_key] = {
            'status': 'starting',
            'progress': 0,
            'output_dir': cache_dir_path,
            'started_at': time.time(),
            'playlist_path': playlist_path
        }
        
        # Start worker thread
        thread = threading.Thread(
            target=self._transcode_worker,
            args=(video_path, video_index, audio_index, cache_dir_path, job_key, duration)
        )
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'url': f'/cache/{cache_dirname}/playlist.m3u8',
            'status': 'processing',
            'progress': 0,
            'message': 'HLS transcoding started',
            'estimated_size': estimated_size
        }
    
    def _transcode_worker(self, video_path, video_index, audio_index, output_dir, job_key, duration):
        """Background worker for HLS transcoding"""
        process = None
        try:
            settings = self._get_h264_settings()
            
            # If audio_index not provided, auto-detect first audio track
            if audio_index is None:
                info = self.ui.track_extractor.get_mkv_info(video_path)
                if info and info.get('audio') and len(info['audio']) > 0:
                    audio_index = info['audio'][0]['index']
                    self.ui.logger.info(f"Auto-detected audio track: {audio_index}")
            
            # HLS segment settings
            segment_time = '4'  # 4-second segments
            segment_list = os.path.join(output_dir, 'playlist.m3u8')
            segment_pattern = os.path.join(output_dir, 'segment_%03d.ts')
            
            # Build FFmpeg command for HLS
            cmd = [
                'ffmpeg',
                '-i', video_path
            ]
            
            # Map streams
            if audio_index is not None:
                cmd.extend(['-map', f'0:{video_index}', '-map', f'0:{audio_index}'])
            else:
                cmd.extend(['-map', f'0:{video_index}'])
            
            # Add scaling filter
            cmd.extend(['-vf', f"scale={settings['scale']}"])
            
            # H.264 video encoding
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', settings['preset'],
                '-crf', settings['crf'],
                '-threads', settings['threads'],
                '-profile:v', settings['profile'],
                '-level', settings['level'],
                '-pix_fmt', 'yuv420p',
                '-b:v', settings['bitrate'],
                '-maxrate', settings['bitrate'],
                '-bufsize', f"{int(float(settings['bitrate'].replace('k', '')) * 2)}k"
            ])
            
            # AAC audio encoding
            if audio_index is not None:
                cmd.extend([
                    '-c:a', 'aac',
                    '-b:a', settings['audio_bitrate'],
                    '-ar', '48000'
                ])
            
            # HLS output settings
            cmd.extend([
                '-f', 'hls',
                '-hls_time', segment_time,
                '-hls_list_size', '0',  # Keep all segments in playlist
                '-hls_segment_filename', segment_pattern,
                '-progress', 'pipe:1',
                '-y',
                segment_list
            ])
            
            self.ui.logger.info(f"Starting HLS transcode: {' '.join(cmd)}")
            
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
            
            if process.returncode == 0 and os.path.exists(segment_list):
                self.transcode_jobs[job_key].update({
                    'status': 'completed',
                    'progress': 100
                })
                
                # Create finished trigger
                trigger_file = os.path.join(output_dir, '.finished')
                open(trigger_file, 'w').close()
                
                self.ui.logger.info(f"HLS transcode completed: {output_dir}")
            else:
                self.transcode_jobs[job_key].update({
                    'status': 'failed',
                    'error': f'FFmpeg failed with code {process.returncode}'
                })
        
        except Exception as e:
            self.ui.logger.error(f"HLS transcode error: {e}")
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
        cache_dirname = self._generate_cache_key(video_path, video_index, audio_index)
        cache_dir_path = os.path.join(self.cache_dir, cache_dirname)
        playlist_path = os.path.join(cache_dir_path, 'playlist.m3u8')
        job_key = f"{video_path}_hls_{video_index}_{audio_index}"
        
        if job_key in self.transcode_jobs:
            job = self.transcode_jobs[job_key]
            return {
                'success': True,
                'url': f'/cache/{cache_dirname}/playlist.m3u8',
                'status': job.get('status', 'processing'),
                'progress': job.get('progress', 0),
                'eta': job.get('eta', 'calculating...')
            }
        
        if os.path.exists(playlist_path):
            return {
                'success': True,
                'url': f'/cache/{cache_dirname}/playlist.m3u8',
                'status': 'completed',
                'progress': 100
            }
        
        return {'success': False, 'status': 'not_found'}
    
    def cancel_transcode(self, video_path, video_index=0, audio_index=None):
        """Cancel transcode and kill FFmpeg process"""
        job_key = f"{video_path}_hls_{video_index}_{audio_index}"
        print(job_key)
        print(self.transcode_jobs)
        
        if job_key not in self.transcode_jobs:
            return {'success': False, 'error': 'No job found'}
        
        job = self.transcode_jobs[job_key]
        
        # KILL THE FFMPEG PROCESS
        if 'process' in job and job['process']:
            try:
                process = job['process']
                self.ui.logger.info(f"Terminating FFmpeg process (PID: {process.pid})...")
                
                # Try graceful termination
                process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                    self.ui.logger.info("Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self.ui.logger.warning("Process didn't stop, force killing...")
                    process.kill()
                    process.wait()
                    self.ui.logger.info("Process force killed")
                    
            except Exception as e:
                self.ui.logger.error(f"Error killing process: {e}")
        
        # DELETE .ts and .m3u8 FILES (keep directory)
        output_dir = job.get('output_dir')
        if output_dir and os.path.exists(output_dir):
            try:
                # Delete all .ts segment files and m3u8 playlist
                for filename in os.listdir(output_dir):
                    filepath = os.path.join(output_dir, filename)
                    if filepath.endswith('.ts') or filepath.endswith('.m3u8'):
                        os.remove(filepath)
                        self.ui.logger.info(f"Deleted: {filename}")
                self.ui.logger.info(f"Cleaned up HLS files in: {output_dir}")
            except Exception as e:
                self.ui.logger.error(f"Error removing HLS files: {e}")
        
        job.update({'status': 'cancelled', 'progress': 0})
        
        self.ui.logger.info(f"Transcode cancelled: {job_key}")
        
        return {'success': True, 'message': 'HLS transcode cancelled and process killed'}
    
    def get_cached_playlist(self, cache_dirname):
        """Get HLS playlist file info"""
        cache_dir_path = os.path.join(self.cache_dir, cache_dirname)
        playlist_path = os.path.join(cache_dir_path, 'playlist.m3u8')
        
        if os.path.isfile(playlist_path):
            return {
                'file_path': playlist_path,
                'content_type': 'application/vnd.apple.mpegurl',
                'is_playlist': True,
                'cache_dir': cache_dir_path
            }
        
        return {'success': False, 'error': 'Playlist not found'}
    
    def get_cached_segment(self, cache_dirname, segment_name):
        """Get HLS segment file info"""
        cache_dir_path = os.path.join(self.cache_dir, cache_dirname)
        segment_path = os.path.join(cache_dir_path, segment_name)
        
        # Security check - ensure segment is in the right directory
        if not os.path.abspath(segment_path).startswith(os.path.abspath(cache_dir_path)):
            return {'success': False, 'error': 'Invalid segment path'}
        
        if os.path.isfile(segment_path):
            file_size = os.path.getsize(segment_path)
            return {
                'file_path': segment_path,
                'content_type': 'video/mp2t',
                'file_size': file_size
            }
        
        return {'success': False, 'error': 'Segment not found'}
