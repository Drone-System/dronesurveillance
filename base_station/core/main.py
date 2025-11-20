from camera.CameraManager import CameraManager
from camera.IpCamera import IpCamera
from DatabaseManager.DatabaseManager import DatabaseManager
from multiprocessing import Process
import ServerBaseStation_pb2_grpc
import ServerBaseStation_pb2
from environment import CONFIG
import asyncio
from time import sleep
import grpc

async def main():
    dbMan = DatabaseManager(

    ) # there must be passed credentials into DbManager read from a .env file

    # DO routine connection to cloud
    # TODO: Change insecure channel https://github.com/grpc/grpc/tree/master/examples/python/auth
    # TODO: Make ip and port configurable in .env
    identifier = -1
    name = CONFIG.get("NAME") #This should be written in a configuaration file
    address = f"{CONFIG.get("GRPC_REMOTE_IP")}:{CONFIG.get("GRPC_REMOTE_PORT")}"
    # while identifier == -1:
    #     sleep(1)
    #     async with grpc.aio.insecure_channel(address) as channel:
    #         stub = ServerBaseStation_pb2_grpc.CloudStub(channel)
    #         identifier =  await stub.Connect(ServerBaseStation_pb2.ConnectToCloudRequest(name=name))

    camManager = CameraManager(identifier, name, dbMan)

    await camManager.run()


    

if __name__ == "__main__":
    asyncio.run(main())