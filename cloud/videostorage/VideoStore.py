import redis
import numpy as np
import cv2
import time
from threading import Thread
import base64
import signal
import sys
import subprocess
from datetime import datetime

r = redis.Redis(host="redisserver", port=6379, db=0, socket_connect_timeout=5)

processes = []

def cleanup(signum, frame):
    print("Stopping and saving all videos...")
    for proc in processes:
        if proc is not None and proc.poll() is None:
            proc.stdin.close()
            proc.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def get_active_streams():
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

def record_stream(key):
    pubsub = r.pubsub()
    pubsub.subscribe(key['channel'])
    
    proc = None
    file_counter = 0
    last_save_time = time.time()
    width, height = None, None

    for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
            
        img_bytes = msg["data"]
        jpg_data = base64.b64decode(img_bytes)
        arr = np.frombuffer(jpg_data, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            continue
        
        if width is None:
            height, width, _ = frame.shape
        
        # Check if 10 seconds have passed
        current_time = time.time()
        if proc is not None and (current_time - last_save_time) >= 60:
            print('new recording saved')
            proc.stdin.close()
            proc.wait()
            processes.remove(proc)
            proc = None
            file_counter += 1
            last_save_time = current_time
        
        # Create new ffmpeg process if needed
        if proc is None:
            video_name = f"videos/{key['basestation_id']}_{key['display_name']}_time_{datetime.utcfromtimestamp(current_time)}.mp4"
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
            processes.append(proc)
            last_save_time = current_time
        
        proc.stdin.write(frame.tobytes())

def recording_manager():
    while True:
        streams = get_active_streams()
        threads = []

        for stream in streams:
            print(stream['channel'])
            t = Thread(target=record_stream, args=(stream,))
            t.start()
            threads.append(t)

        try:
            for t in threads:
                t.join()
        except Exception as e:
            print("Exception:", e)
        

if __name__ == "__main__":
    recording_manager()