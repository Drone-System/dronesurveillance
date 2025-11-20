import psycopg2
from environment import CONFIG
from camera.IpCamera import IpCamera

class DatabaseManager:
    
    def __init__(self):
        self.conn = psycopg2.connect(database = CONFIG.get('DB_NAME'),
                                        user = CONFIG.get('DB_USER'),
                                        host = CONFIG.get('DB_HOST'),
                                        password = CONFIG.get('DB_PASSWORD'),
                                        port = CONFIG.get('DB_PORT'))
        self.cursor = self.conn.cursor()

    def pollCameras(self):
        self.cursor.execute("SELECT id FROM devices")
        ids = self.cursor.fetchall()
        print(ids)
        return [cam[0] for cam in ids]

    def updateProtocols(self, protocols: dict):
        pass

    def getCameraById(self, cam: int):
        self.cursor.execute(f"Select * from devices where id = {cam}")
        cams: tuple = self.cursor.fetchall()
        print([cam[0] for cam in cams])

        return IpCamera("udp://0.0.0.0:5000")

    def GetCameraNameById(self, cam_id: int):
        return "Some Name"
