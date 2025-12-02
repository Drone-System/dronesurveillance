import asyncio
from drone.WebRtcDrone import DroneWebRTCProducer
from drone.DjiTello import DjiTelloDrone
async def main():
    p = DroneWebRTCProducer(-1, DjiTelloDrone, 'stream')
    await p.start(asyncio.Event())

if __name__ == "__main__":
    asyncio.run(main())