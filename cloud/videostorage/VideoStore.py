import redis
import numpy as np
import cv2
import time
from threading import Thread, Lock, Event
import base64
import signal
import sys
import subprocess
from datetime import datetime
from collections import defaultdict

r = redis.Redis(host="redisserver", port=6379, db=0, socket_connect_timeout=5)

class StreamRecorder:
    def __init__(self, idle_timeout=5.0):
        """
        Initialize the stream recorder.
        
        Args:
            idle_timeout: Seconds of inactivity before stopping recording
        """
        self.active_threads = {}
        self.stop_flags = {}
        self.last_activity = {}
        self.processes = []
        self.global_lock = Lock()
        self.idle_timeout = idle_timeout
        
    def cleanup(self, signum=None, frame=None):
        """Stop all recordings and clean up processes."""
        print("Stopping and saving all videos...")
        self.stop_all()
        
        with self.global_lock:
            for proc in self.processes:
                if proc is not None and proc.poll() is None:
                    try:
                        proc.stdin.close()
                        proc.wait(timeout=2.0)
                    except:
                        proc.kill()
        sys.exit(0)
    
    def get_active_streams(self):
        """
        Discover all active video streams by checking for latest_frame keys in Redis
        Only returns streams that have active heartbeats (updated within last 5 seconds)
        Returns a list of stream channel names
        """
        streams = []
        
        # Get all keys that match the pattern 'latest_frame_*'
        keys = r.keys('latest_frame_*')
        for key in keys:
            # Extract channel name from key (remove 'latest_frame_' prefix)
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            channel_name = key_str.replace('latest_frame_', '')
            
            # Check if stream has an active heartbeat
            heartbeat_key = f'heartbeat_{channel_name}'
            heartbeat = r.get(heartbeat_key)
            
            # Only include streams with active heartbeat
            if heartbeat:
                fields = channel_name.split("_")
                display_name = fields[2]
                b_id = fields[0]
                streams.append({
                    'channel': channel_name,
                    'display_name': display_name,
                    'basestation_id': b_id
                })

        streams.sort(key=lambda x: x['display_name'])
        
        return streams
    
    def record_stream(self, stream_info):
        """
        Records video from a specific stream until idle.
        This runs in a separate thread for each stream.
        
        Args:
            stream_info: Dictionary with channel, display_name, basestation_id
        """
        channel = stream_info['channel']
        print(f"[{channel}] Started recording thread")
        
        pubsub = r.pubsub()
        pubsub.subscribe(channel)
        
        proc = None
        file_counter = 0
        last_save_time = time.time()
        width, height = None, None
        
        # Set initial activity time
        with self.global_lock:
            self.last_activity[channel] = time.time()
        
        try:
            for msg in pubsub.listen():
                # Check if stop flag is set
                if self.stop_flags[channel].is_set():
                    print(f"[{channel}] Stop signal received")
                    break
                
                if msg["type"] != "message":
                    continue
                
                try:
                    img_bytes = msg["data"]
                    jpg_data = base64.b64decode(img_bytes)
                    arr = np.frombuffer(jpg_data, np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        # Check for idle timeout on bad frame
                        with self.global_lock:
                            idle_duration = time.time() - self.last_activity[channel]
                            if idle_duration >= self.idle_timeout:
                                print(f"[{channel}] No valid frames for {idle_duration:.1f}s, stopping...")
                                break
                        continue
                    
                    # Update activity time on successful frame
                    with self.global_lock:
                        self.last_activity[channel] = time.time()
                    
                    if width is None:
                        height, width, _ = frame.shape
                    
                    # Check if 10 seconds have passed
                    current_time = time.time()
                    if proc is not None and (current_time - last_save_time) >= 10:
                        print(f'[{channel}] New recording segment saved')
                        proc.stdin.close()
                        proc.wait()
                        with self.global_lock:
                            self.processes.remove(proc)
                        proc = None
                        file_counter += 1
                        last_save_time = current_time
                    
                    # Create new ffmpeg process if needed
                    if proc is None:
                        timestamp = datetime.utcfromtimestamp(current_time).strftime('%Y%m%d_%H%M%S')
                        video_name = f"videos/{stream_info['basestation_id']}_{stream_info['display_name']}_time_{timestamp}.mp4"
                        proc = subprocess.Popen([
                            'ffmpeg', '-y',
                            '-f', 'rawvideo',
                            '-vcodec', 'rawvideo',
                            '-pix_fmt', 'bgr24',
                            '-s', f'{width}x{height}',
                            '-r', '30',
                            '-i', '-',
                            '-c:v', 'libx264',
                            '-pix_fmt', 'yuv420p',
                            '-preset', 'ultrafast',
                            video_name
                        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                        with self.global_lock:
                            self.processes.append(proc)
                        last_save_time = current_time
                        print(f"[{channel}] Started new video segment: {video_name}")
                    
                    proc.stdin.write(frame.tobytes())
                    
                except Exception as e:
                    print(f"[{channel}] Error processing frame: {e}")
                    # Check for idle timeout on error
                    with self.global_lock:
                        idle_duration = time.time() - self.last_activity[channel]
                        if idle_duration >= self.idle_timeout:
                            print(f"[{channel}] Errors for {idle_duration:.1f}s, stopping...")
                            break
                    continue
                    
        except Exception as e:
            print(f"[{channel}] Fatal error: {e}")
        finally:
            # Cleanup
            if proc is not None:
                try:
                    proc.stdin.close()
                    proc.wait(timeout=2.0)
                    with self.global_lock:
                        if proc in self.processes:
                            self.processes.remove(proc)
                except:
                    proc.kill()
            
            pubsub.unsubscribe()
            pubsub.close()
            self._finalize_recording(channel)
    
    def _finalize_recording(self, channel):
        """
        Finalize a recording session.
        
        Args:
            channel: The channel name to finalize
        """
        with self.global_lock:
            print(f"[{channel}] Recording complete")
            
            # Cleanup
            if channel in self.active_threads:
                del self.active_threads[channel]
            if channel in self.stop_flags:
                del self.stop_flags[channel]
            if channel in self.last_activity:
                del self.last_activity[channel]
    
    def start_recording(self, stream_info):
        """
        Start a recording thread for a stream if one doesn't exist.
        
        Args:
            stream_info: Dictionary with channel, display_name, basestation_id
        """
        channel = stream_info['channel']
        
        with self.global_lock:
            # Check if thread already exists and is alive
            if channel in self.active_threads:
                if self.active_threads[channel].is_alive():
                    print(f"[{channel}] Thread already running")
                    return
            
            # Create new thread
            self.stop_flags[channel] = Event()
            self.last_activity[channel] = time.time()
            
            thread = Thread(
                target=self.record_stream,
                args=(stream_info,),
                daemon=True,
                name=f"recorder_{channel}"
            )
            
            self.active_threads[channel] = thread
            thread.start()
            print(f"[{channel}] Started new recording thread")
    
    def stop_recording(self, channel):
        """
        Stop recording a specific stream.
        
        Args:
            channel: The channel name to stop
        """
        with self.global_lock:
            if channel in self.stop_flags:
                self.stop_flags[channel].set()
                print(f"[{channel}] Stop signal sent")
    
    def stop_all(self):
        """Stop all active recording threads."""
        print("Stopping all recording threads...")
        
        with self.global_lock:
            for channel in list(self.stop_flags.keys()):
                self.stop_flags[channel].set()
        
        # Wait for threads to finish
        for thread in list(self.active_threads.values()):
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        print("All threads stopped")
    
    def get_active_recordings(self):
        """Get set of currently active recording channel names."""
        with self.global_lock:
            return {channel for channel, thread in self.active_threads.items() 
                   if thread.is_alive()}
    
    def recording_manager(self):
        """
        Main monitoring loop that checks for active streams and starts
        recording threads as needed.
        """
        stream_dict = {}
        print("Starting stream recording manager...")
        
        try:
            while True:
                streams = self.get_active_streams()
                new_streams = []

                # Find new streams not yet being recorded
                for stream in streams:
                    if stream['channel'] not in stream_dict:
                        stream_dict[stream['channel']] = stream
                        new_streams.append(stream)

                if len(new_streams) > 0:
                    print(f"Found {len(new_streams)} new stream(s)")
                    for stream in new_streams:
                        print(f"  - {stream['channel']}")

                # Start recording thread for each new stream
                for stream in new_streams:
                    self.start_recording(stream)
                
                # Clean up dead streams from dict
                active_channels = {s['channel'] for s in streams}
                dead_channels = [ch for ch in stream_dict.keys() if ch not in active_channels]
                for ch in dead_channels:
                    del stream_dict[ch]
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\nStopping manager...")
            self.stop_all()


if __name__ == "__main__":
    recorder = StreamRecorder(idle_timeout=5.0)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, recorder.cleanup)
    signal.signal(signal.SIGTERM, recorder.cleanup)
    
    # Start monitoring
    recorder.recording_manager()