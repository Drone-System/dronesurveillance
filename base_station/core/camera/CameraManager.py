# from ..DatabaseManager import DatabaseManager
from .Camera import Camera
from kafka import KafkaProducer 
from dotenv import load_dotenv
import os

class CameraManager:
    
    def __init__(self, id, name):
        load_dotenv()

        self.cameras = []
        self.topic = id
        self.name = name
        # self.producer = KafkaProducer(bootstrap_servers=f"{os.getenv(KAFKA_BROKER_IP)}:{os.getenv(KAFKA_BROKER_PORT)}")
        self.producer = KafkaProducer(bootstrap_servers="localhost:9092")

    def registerCamera(self, cam: Camera):
        cam.connect()
        self.cameras.append(cam)
    
    def removeCamera(self, cam):
        cam.disconnect()
        self.cameras.remove(cam)

    def processCameras(self):
        for cam in self.cameras:
            ret, frame = cam.recv()
            if not ret:
                print(f"Error in camera: {cam.id}")
                continue
            
            self.producer.send("_".join([str(self.topic), str(cam.id)]), frame)
            

