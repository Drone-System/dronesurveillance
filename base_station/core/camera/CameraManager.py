# from ..DatabaseManager import DatabaseManager
from .Camera import Camera
from kafka import KafkaProducer 
from dotenv import load_dotenv
import os
import threading
from multiprocessing import Process
from ..DatabaseManager.DatabaseManager import DatabaseManager
from .Protocol import cameraTypeTranslator
from .WebRtcProducer import WebRTCProducer
from multiprocessing import Process, Queue
import asyncio

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
            cameras: list[int] = self.dbMan.pollCameras()
            for cam in cameras:
                if cam not in self.cameras:
                    newCamera = self.__registerCamera(cam)
                    # self.cameras[cam] = Process()
                    pass
            for cam in self.cameras.keys():
                if cam not in cameras:
                    # stop process
                    self.__removeCamera(cam)

            sleep(10) # check every 10 seconds


    def __registerCamera(self, cam: int):
        camera = self.dbMan.getCameraById(cam) # somewhere inside this should call protocol transformer
        cam_name = self.dbMan.GetCameraNameById(cam)
        producer = WebRTCProducer(basestation_id=self.identifier, source=camera, stream_name=cam_name)
        # self.cameras[cam] = multiprocessing.Process() This should span a process where the webrtc producer runs
        q = Queue(maxsize=3)
        p = Process(target=asyncio.run, args=(producer.start(q)))
        self.cameras[cam] = (p, q)
        q.start()
        p.start()

    
    def __removeCamera(self, cam):
        process, q = self.cameras[cam]
        q.put(1)
        self.cameras.pop(cam)
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