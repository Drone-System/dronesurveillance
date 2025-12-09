from camera.CameraManager import CameraManager
from drone.DroneManager import DroneManager
from camera.IpCamera import IpCamera
from DatabaseManager.DatabaseManager import DatabaseManager
from multiprocessing import Process
import ServerBaseStation_pb2_grpc
import ServerBaseStation_pb2
from environment import CONFIG
import asyncio
from time import sleep
import grpc
import _credentials

async def main():
    creds = grpc.ssl_channel_credentials(_credentials.ROOT_CERTIFICATE)
    dbMan = DatabaseManager(

    ) # there must be passed credentials into DbManager read from a .env file

    identifier = -1
    name = CONFIG.get("BASESTATION_NAME") #This should be written in a configuaration file
    password = CONFIG.get("BASESTATION_PASSWORD")
    address = f"{CONFIG.get('GRPC_REMOTE_IP')}:{CONFIG.get('GRPC_REMOTE_PORT')}"
    while identifier == -1:
        sleep(1)
        async with grpc.aio.secure_channel(address, creds) as channel:
            stub = ServerBaseStation_pb2_grpc.CloudStub(channel)
            response =  await stub.Connect(ServerBaseStation_pb2.ConnectToCloudRequest(name=name, password=password))
            identifier = response.id

    print("Got Id:", identifier)
    camManager = CameraManager(identifier, name, dbMan)
    droneManager = DroneManager(identifier, name, dbMan)
    print("Started")
    await asyncio.gather(camManager.run(), droneManager.run())


    

if __name__ == "__main__":
    asyncio.run(main())