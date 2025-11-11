# from ..DatabaseManager import DatabaseManager
from .Camera import Camera
from kafka import KafkaProducer 
from dotenv import load_dotenv
import os
import threading

class CameraManager:
    
    def __init__(self, id, name):
        load_dotenv()

        self.cameras = []
        self.topic = id
        self.name = name
        # self.producer = KafkaProducer(bootstrap_servers=f"{os.getenv(KAFKA_BROKER_IP)}:{os.getenv(KAFKA_BROKER_PORT)}")
        # self.producer = KafkaProducer(bootstrap_servers="10.92.0.81:9092", enable_idempotence=True)
        self.producer = KafkaProducer(bootstrap_servers="localhost:9092", enable_idempotence=True)

    def registerCamera(self, cam: Camera):
        cam.connect()
        self.cameras.append(cam)
    
    def removeCamera(self, cam):
        cam.disconnect()
        self.cameras.remove(cam)

    def processCameras(self):
        threads = [None for _ in self.cameras]
        for i in range(len(self.cameras)):
            threads[i] = threading.Thread(target=self.processCamera, args=(i, ))
            threads[i].start()
            
        for i in range(len(self.cameras)):
            threads[i].join()


    def processCamera(self, a):
        cam = self.cameras[a]
        count = 0
        while count < 20000:
            ret, frame = cam.recv()
            if not ret:
                print(f"Error in camera: {cam.id}")
                continue
            self.producer.send("_".join([str(self.topic), str(cam.id)]), frame)
            count += 1