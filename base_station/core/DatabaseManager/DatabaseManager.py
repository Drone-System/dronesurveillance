import psycopg2
from environment import CONFIG
from camera.IpCamera import IpCamera

class DatabaseManager:
    
    def __init__(self):
        self.conn = psycopg2.connect(host = CONFIG.get('DB_HOST'),
                                        port = CONFIG.get('DB_PORT'),
                                        user = CONFIG.get('DB_USER'),
                                        password = CONFIG.get('DB_PASSWORD'),
                                        database = CONFIG.get('DB_NAME'))
        self.cursor = self.conn.cursor()
        pass

    def pollCameras(self):
        self.cursor.execute("SELECT id FROM devices")
        ids = self.cursor.fetchall()
        # ids = [(6, )]
        print(ids)

        return [cam[0] for cam in ids]

    def updateProtocols(self, protocols: dict):
        pass

    def getCameraById(self, cam: int):
        self.cursor.execute(f"Select * from devices where id = {cam}")
        curr_camera: tuple = self.cursor.fetchone()
        print(curr_camera)
        # print(":".join([cam[2], cam[3]]))
        if cam == 7:
            return IpCamera(2)
        else:
            return IpCamera(0)

    def GetCameraNameById(self, cam_id: int):
        return "Some Name"
