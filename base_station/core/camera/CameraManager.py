# from ..DatabaseManager import DatabaseManager
from .Camera import Camera
from kafka import KafkaProducer 
from dotenv import load_dotenv
import os
import threading
from multiprocessing import Process
from ..DatabaseManager.DatabaseManager import DatabaseManager
from .Protocol import cameraTypeTranslator

class CameraManager:
    
    def __init__(self, id: str, name: str, dbMan: DatabaseManager):
        load_dotenv()
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
                    pass
            sleep(10) # check every 10 seconds
        pass

    def __registerCamera(self, cam: int):
        camera = self.dbMan.getCameraById(cam) # somewhere inside this should call protocol transformer

        cam.connect()
        self.cameras.append(cam)

    def __registerCamera(self, cam: int):
        camera = self.dbMan.getCameraById(cam)
        
        cam.connect()
    
    def __removeCamera(self, cam):
        cam.disconnect()
        self.cameras.remove(cam)

    def __processCameras(self):
        threads = [None for _ in self.cameras]
        for i in range(len(self.cameras)):
            threads[i] = threading.Thread(target=self.processCamera, args=(i, ))
            threads[i].start()
            
        for i in range(len(self.cameras)):
            threads[i].join()


    def __processCamera(self, a):
        cam = self.cameras[a]
        count = 0
        while count < 20000:
            ret, frame = cam.recv()
            if not ret:
                print(f"Error in camera: {cam.id}")
                continue
            self.producer.send("_".join([str(self.topic), str(cam.id)]), frame)
            count += 1