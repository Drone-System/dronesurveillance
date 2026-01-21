import os
import asyncio
import base64
import time
import io
from PIL import Image
import numpy as np
import cv2
import redis.asyncio as redis
from ultralytics import YOLO
from alert import send_alert_email
from queue import Queue
from threading import Thread

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
REDIS_DB = 0
MODEL_PATH = "yolov8n.pt"
THREAT_CLASSES = os.getenv("THREAT_CLASSES", "person,knife,gun").split(",")
CONFIDENCE_THRESHOLD = 0.50
COOLDOWN_SECONDS = 2
PROCESS_INTERVAL = 0.2
SHOW_DETECTIONS = os.getenv("SHOW_DETECTIONS", "true").lower() == "true"

cooldowns = {}
model = YOLO(MODEL_PATH)
model_names = model.names

# Queue for passing frames to display thread
display_queue = Queue(maxsize=10)

def display_thread():
    """Separate thread to handle OpenCV GUI events properly."""
    print("[DISPLAY] Display thread started")
    windows = {}
    last_detection_time = {}  # Track last detection time per channel
    current_frames = {}  # Store current frame per channel
    
    while True:
        try:
            # Non-blocking get with timeout
            item = display_queue.get(timeout=0.1)
            
            if item is None:  # Shutdown signal
                break
            
            channel, frame = item
            window_name = f"THREAT - {channel}"
            
            if window_name not in windows:
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                windows[window_name] = True
            
            # Update last detection time and current frame
            last_detection_time[channel] = time.time()
            current_frames[channel] = frame
            cv2.imshow(window_name, frame)
            
        except:
            pass  # Queue empty, continue
        
        # Check all channels for timeout (20 seconds without detection)
        current_time = time.time()
        for channel, last_time in list(last_detection_time.items()):
            if (current_time - last_time) > 20:
                window_name = f"THREAT - {channel}"
                if window_name in windows and channel in current_frames:
                    # Create black frame with same dimensions as last frame
                    black_frame = np.zeros_like(current_frames[channel])
                    cv2.imshow(window_name, black_frame)
                    # Update frame to black so we don't recreate it every loop
                    current_frames[channel] = black_frame
        
        # Service all OpenCV windows
        key = cv2.waitKey(1)
        if key == 27:  # ESC to close
            break
    
    cv2.destroyAllWindows()
    print("[DISPLAY] Display thread stopped")

def decode_jpg(b64):
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(img)[:, :, ::-1]

def encode_jpg(img):
    """Encode OpenCV image (BGR) to base64 JPEG string."""
    img_rgb = img[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def detect_threat(results):
    out = []
    for box in results[0].boxes:
        name = model_names[int(box.cls)]
        conf = float(box.conf)
        if conf >= CONFIDENCE_THRESHOLD and name in THREAT_CLASSES:
            out.append({"name": name, "conf": conf})
    return out

async def process_stream(channel, r):
    """Runs YOLO on the latest frame of this stream every N milliseconds."""
    print(f"[DETECTOR] Watching stream: {channel}")
    while True:
        frame_key = f"latest_frame_{channel}"
        heartbeat_key = f"heartbeat_{channel}"
        
        # confirm active stream
        hb = await r.get(heartbeat_key)
        if hb is None:
            await asyncio.sleep(1)
            continue
        
        # read frame
        b64 = await r.get(frame_key)
        if not b64:
            await asyncio.sleep(0.1)
            continue
        
        try:
            frame = decode_jpg(b64)
        except Exception:
            await asyncio.sleep(0.1)
            continue
        
        # cooldown
        last = cooldowns.get(channel, 0)
        if (time.time() - last) < COOLDOWN_SECONDS:
            await asyncio.sleep(PROCESS_INTERVAL)
            continue
        
        # run YOLO
        results = model.predict(frame, verbose=False)
        threats = detect_threat(results)
        
        if threats:
            print(f"[{channel}] THREAT DETECTED:", threats)
            cooldowns[channel] = time.time()
            
            # Get annotated image with bounding boxes
            annotated_frame = results[0].plot()
            
            # Send to display thread if enabled
            if SHOW_DETECTIONS:
                try:
                    display_queue.put_nowait((channel, annotated_frame))
                except:
                    pass  # Queue full, skip this frame
            
            # Encode annotated frame to base64
            annotated_b64 = encode_jpg(annotated_frame)
            
            # Store annotated frame in Redis
            annotated_key = f"threat_detection_{channel}"
            await r.set(annotated_key, annotated_b64, ex=300)
            
            alert_msg = {
                "channel": channel,
                "detections": threats,
                "timestamp": int(time.time()),
                "annotated_frame_key": annotated_key
            }
            
            # publish alert
            await r.publish("alerts", str(alert_msg))
            
            # send email
            send_alert_email(channel, threats)
        
        await asyncio.sleep(PROCESS_INTERVAL)

async def stream_discovery():
    """Auto-detect new streams and spawn detector tasks."""
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    known = set()
    print("[DETECTOR] Running auto-discovery...")
    
    while True:
        keys = await r.keys("latest_frame_*")
        channels = [key.replace("latest_frame_", "") for key in keys]
        
        # start detectors for new channels
        for ch in channels:
            if ch not in known:
                known.add(ch)
                asyncio.create_task(process_stream(ch, r))
        
        await asyncio.sleep(2)

def main():
    # Start display thread if enabled
    display_worker = None
    if SHOW_DETECTIONS:
        display_worker = Thread(target=display_thread, daemon=True)
        display_worker.start()
    
    try:
        asyncio.run(stream_discovery())
    except KeyboardInterrupt:
        print("\n[DETECTOR] Shutting down...")
    finally:
        # Signal display thread to stop
        if SHOW_DETECTIONS and display_worker:
            display_queue.put(None)
            display_worker.join(timeout=2)

if __name__ == "__main__":
    main()