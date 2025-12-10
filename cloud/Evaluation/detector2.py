# detector_read_from_keys.py
import os
import asyncio
import base64
import time
import io
from PIL import Image
import numpy as np
import redis.asyncio as redis
from ultralytics import YOLO

from alert import send_alert_email

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
REDIS_DB = 0
MODEL_PATH = "yolov8n.pt"
THREAT_CLASSES = os.getenv("THREAT_CLASSES", "person,knife,gun").split(",")
CONFIDENCE_THRESHOLD = 0.50
COOLDOWN_SECONDS = 20
PROCESS_INTERVAL = 0.2

cooldowns = {}
model = YOLO(MODEL_PATH)
model_names = model.names

def decode_jpg(b64):
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(img)[:, :, ::-1]

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
            annotated_frame = results[0].plot()  # Returns image with boxes drawn
            # send email
            send_alert_email(channel, threats, annotated_frame)

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
    asyncio.run(stream_discovery())

if __name__ == "__main__":
    main()
