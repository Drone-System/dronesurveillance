# from ..DatabaseManager import DatabaseManager
# from .Camera import Camera
from dotenv import load_dotenv
import os
import threading
from DatabaseManager.DatabaseManager import DatabaseManager
# from Protocol import cameraTypeTranslator
from drone.WebRtcDrone import DroneWebRTCProducer
import asyncio
from time import sleep
from aiortc.contrib.media import MediaPlayer
# from camdroneera.IpCamera import IpCamera

class DroneManager:
    
    def __init__(self, id: str, name: str, dbMan: DatabaseManager):
        '''
        self.cameras is a dictionary where
            - Keys: camera ids
            - Values:  Tuple ( Process, Queue )

        Process denotes the process capturing and sending video via webrtc
        Queue denotes the queue used for communication between the main process and the sub-process
        '''
        self.drones = {}
        self.identifier = id
        self.name = name
        self.dbMan = dbMan
    
    async def run(self):

        while True:
            try:
                drones: list[int] = self.dbMan.pollDrones()
                to_add = {}
                to_remove = []
                for drone in drones:
                    if drone not in self.drones:
                        # start process
                        print(f"New drone {drone} detected.")
                        to_add.update(self.__registerDrone(drone, asyncio.get_running_loop()))

                for drone in self.drones.keys():
                    if drone not in drones:
                        # stop process
                        print(f"Drone {drone} removed.")
                        await self.__removeDrone(drone)
                        to_remove.append(drone)
                
                self.drones.update(to_add)
                for c in to_remove:
                    self.drones.pop(c)
                await asyncio.sleep(10) # check every 10 seconds

            except KeyboardInterrupt:
                print("\nStopping producer...")
                break
            except Exception as e:
                print("EXCEPTION: ", e)
                break

        print("Finally")
        print(self.drones)
        for task, signal in self.drones.values():
            signal.set()
            await task
            exit(0)
        


    def __registerDrone(self, drone_id: int, event_loop):
        drone = self.dbMan.getDroneById(drone_id) # somewhere inside this should call protocol transformer
        # camera = IpCamera("")
        drone_name = self.dbMan.GetDroneNameById(drone)
        print("Opened cam")
        producer = DroneWebRTCProducer(basestation_id=self.identifier, source=drone, stream_name=drone_name)
        # self.cameras[cam] = multiprocessing.Process() This should span a process where the webrtc producer runs
        # q = Queue(maxsize=3)
        signal = asyncio.Event()
        # await producer.start(signal)
        print("Starting process...")
        # p = Process(target=self.__run_producer, args=(producer, q), daemon=False)
        task = event_loop.create_task(producer.start(signal))
        print("created")
        return {drone_id: (task, signal)}

    # def __run_producer(self, producer, signal):
    #     asyncio.run(producer.start(signal))
    
    async def __removeDrone(self, drone_id: int):
        process, q = self.drones[drone_id]
        q.set()
        # self.cameras.pop(cam)
        await process
        
