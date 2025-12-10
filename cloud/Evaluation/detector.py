# detector.py
import os
import asyncio
import base64
import io
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image
import redis.asyncio as redis
from ultralytics import YOLO

from alert import send_alert_email

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CHANNEL_PATTERN = os.getenv("CHANNEL_PATTERN", "*")
MODEL_PATH = os.getenv("YOLO_MODEL", "yolov8n.pt")
THREAT_CLASSES = os.getenv("THREAT_CLASSES", "person,knife,gun").split(",")
CONFIDENCE_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.5"))
PROCESS_EVERY_N = int(os.getenv("PROCESS_EVERY_N", "3"))  # process 1 of every N frames

print("Loading YOLO model:", MODEL_PATH)
model = YOLO(MODEL_PATH)
model_names = model.names if hasattr(model, "names") else {}

executor = ThreadPoolExecutor(max_workers=2)
frame_counters = {}

def decode_jpg_base64(b64_string):
    jpg = base64.b64decode(b64_string)
    img = Image.open(io.BytesIO(jpg)).convert("RGB")
    arr = np.asarray(img)[:, :, ::-1]  # RGB->BGR
    return arr

def is_threat(result):
    detected = []
    try:
        boxes = result.boxes
        for box in boxes:
            conf = float(box.conf[0]) if hasattr(box, "conf") else float(box.conf)
            cls_idx = int(box.cls[0]) if hasattr(box, "cls") else int(box.cls)
            name = model_names.get(cls_idx, str(cls_idx))
            if conf >= CONFIDENCE_THRESHOLD and name in THREAT_CLASSES:
                detected.append({"name": name, "conf": conf})
    except Exception:
        pass
    return detected



last_alert_time = {}

async def handle_frame(b64_str, channel_name, r):
    """
    Handle a single frame from Redis, run YOLO detection, and send alerts
    with cooldown to avoid spamming.
    """
    # --- Basic frame sampling ---
    c = frame_counters.get(channel_name, 0) + 1
    frame_counters[channel_name] = c
    if (c % PROCESS_EVERY_N) != 0:
        return

    # --- Decode image ---
    try:
        img = decode_jpg_base64(b64_str)
    except Exception as e:
        print(f"[{channel_name}] decode error: {e}")
        return

    # --- Run YOLO safely in executor ---
    loop = asyncio.get_event_loop()
    try:
        def run_inference():
            res = model.predict(img, conf=CONFIDENCE_THRESHOLD, verbose=False)
            if hasattr(res, "__iter__") and not isinstance(res, list):
                res = list(res)
            if isinstance(res[0], list):
                return res[0][0]
            return res[0]

        result = await loop.run_in_executor(executor, run_inference)

        # --- Detect threats ---
        detected = is_threat(result)
        if detected:
            now = time.time()
            cooldown = 10  # seconds between alerts
            last_time = last_alert_time.get(channel_name, 0)

            if now - last_time >= cooldown:
                last_alert_time[channel_name] = now

                print(f"[{channel_name}] Threat detected: {detected}")
                alert_payload = {
                    "channel": channel_name,
                    "detections": detected,
                    "timestamp": int(now)
                }
                await r.publish("alerts", str(alert_payload))

                # Send email in executor (non-blocking)
                await loop.run_in_executor(executor, send_alert_email, channel_name, detected)
            else:
                # Suppress spam alerts
                pass

    except Exception as e:
        print(f"[{channel_name}] detection error: {e}")
async def redis_subscriber():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    pubsub = r.pubsub()
    print("Subscribing with pattern:", CHANNEL_PATTERN)
    await pubsub.psubscribe(CHANNEL_PATTERN)

    async for message in pubsub.listen():
        try:
            mtype = message.get("type")
            if mtype not in ("pmessage", "message"):
                continue
            channel = message.get("channel")
            data = message.get("data")
            if isinstance(channel, bytes):
                channel = channel.decode()
            if isinstance(data, bytes):
                data = data.decode()
            if data is None or data == 1:
                continue
            asyncio.create_task(handle_frame(data, channel, r))
        except Exception as e:
            print("listen error:", e)
            await asyncio.sleep(0.1)

def main():
    print("Starting detector...")
    asyncio.run(redis_subscriber())

if __name__ == "__main__":
    main()
