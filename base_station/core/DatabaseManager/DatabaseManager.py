import psycopg
from environment import CONFIG
from camera.CameraFactory import CameraFactory
from drone.DroneFactory import DroneFactory
from drone.DjiTello import DjiTelloDrone
import json

class DatabaseManager:
    
    def __init__(self):
        self.conn = psycopg.connect(host = CONFIG.get('DB_HOST'),
                                        port = CONFIG.get('DB_PORT'),
                                        user = CONFIG.get('DB_USER'),
                                        password = CONFIG.get('DB_PASSWORD'),
                                        dbname = CONFIG.get('DB_NAME'))
        self.cursor = self.conn.cursor()

    def pollCameras(self):
        self.cursor.execute("SELECT id FROM cameras")
        rows = self.cursor.fetchall()
        # ids = [(6, )]
        print("Cameras:", rows)

        return [row[0] for row in rows]


    def getCameraById(self, cam_id: int):
        self.cursor.execute(f"Select camera_type, config from cameras where id = {cam_id}")
        curr_camera: tuple = self.cursor.fetchone()
        print(curr_camera)
        return CameraFactory.newCamera(camera_type=curr_camera[0], config=curr_camera[1])
        # # print(":".join([cam[2], cam[3]]))
        # if cam == 7:
        #     return IpCamera(2)
        # else:
        #     return IpCamera(0)

    def GetCameraNameById(self, cam_id: int):
        self.cursor.execute(f"select name from cameras where id = {cam_id}")
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def pollDrones(self):
        self.cursor.execute("SELECT id FROM drones")
        rows = self.cursor.fetchall()
        # ids = [(6, )]
        print("Drones:", rows)

        return [row[0] for row in rows]

    def getDroneById(self, drone_id: int):
        self.cursor.execute(f"Select drone_type, config from drones where id = {drone_id}")
        curr_drone: tuple = self.cursor.fetchone()
        print(curr_drone)
        return DroneFactory.newDrone(drone_type=curr_drone[0], config=curr_drone[1])

    def getDroneNameById(self, drone_id):
        self.cursor.execute(f"select name from drones where id = {drone_id}")
        row = self.cursor.fetchone()
        return row[0] if row else None
