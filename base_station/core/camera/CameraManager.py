# from ..DatabaseManager import DatabaseManager
# from .Camera import Camera
from kafka import KafkaProducer 
from dotenv import load_dotenv
import os
import threading
from multiprocessing import Process
from DatabaseManager.DatabaseManager import DatabaseManager
# from Protocol import cameraTypeTranslator
from communication.WebRtcProducer import WebRTCProducer
from multiprocessing import Process, Queue
import asyncio
from time import sleep
from aiortc.contrib.media import MediaPlayer
from camera.IpCamera import IpCamera

class CameraManager:
    
    def __init__(self, id: str, name: str, dbMan: DatabaseManager):
        '''
        self.cameras is a dictionary where
            - Keys: camera ids
            - Values:  Tuple ( Process, Queue )

        Process denotes the process capturing and sending video via webrtc
        Queue denotes the queue used for communication between the main process and the sub-process
        '''
        self.cameras = {}
        self.identifier = id
        self.name = name
        self.dbMan = dbMan
    
    def run(self):

        while True:
            try:
                cameras: list[int] = self.dbMan.pollCameras()
                to_add = {}
                to_remove = []
                for cam in cameras:
                    if cam not in self.cameras:
                        # start process
                        print(f"New Camera {cam} detected.")
                        to_add.update(self.__registerCamera(cam))

                for cam in self.cameras.keys():
                    if cam not in cameras:
                        # stop process
                        print(f"Camera {cam} removed.")
                        self.__removeCamera(cam)
                        to_remove.append(cam)
                
                self.cameras.update(to_add)
                for c in to_remove:
                    self.cameras.pop(c)
                sleep(10) # check every 10 seconds

            except KeyboardInterrupt:
                print("\nStopping producer...")
                break
            except Exception as e:
                print("EXCEPTION: ", e)
                break

        print("Finally")
        print(self.cameras)
        for p, q in self.cameras.values():
            q.put(1)
            p.join()
            exit(0)
        


    def __registerCamera(self, cam: int):
        # camera = self.dbMan.getCameraById(cam) # somewhere inside this should call protocol transformer
        cam_name = self.dbMan.GetCameraNameById(cam)
        source = IpCamera("udp://127.0.0.1:3000")
        # source = MediaPlayer("/dev/video2").video
        print("Opened cam")
        producer = WebRTCProducer(basestation_id=self.identifier, source=source, stream_name=cam_name)
        # self.cameras[cam] = multiprocessing.Process() This should span a process where the webrtc producer runs
        q = Queue(maxsize=3)
        print("Starting process...")
        p = Process(target=self.__run_producer, args=(producer, q), daemon=False)
        p.start()
        return {cam: (p, q)}

    def __run_producer(self, producer, q):
        asyncio.run(producer.start(q))
    
    def __removeCamera(self, cam: int):
        process, q = self.cameras[cam]
        q.put(1)
        # self.cameras.pop(cam)
        process.join()
        

    # def __processCameras(self):
    #     threads = [None for _ in self.cameras]
    #     for i in range(len(self.cameras)):
    #         threads[i] = threading.Thread(target=self.processCamera, args=(i, ))
    #         threads[i].start()
            
    #     for i in range(len(self.cameras)):
    #         threads[i].join()


    # def __processCamera(self, a):
    #     cam = self.cameras[a]
    #     count = 0
    #     while count < 20000:
    #         ret, frame = cam.recv()
    #         if not ret:
    #             print(f"Error in camera: {cam.id}")
    #             continue
    #         self.producer.send("_".join([str(self.topic), str(cam.id)]), frame)
    #         count += 1