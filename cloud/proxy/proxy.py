from DroneWebRtc import DroneWebRtc
from WebRtcReceiver import WebRTCReceiver
from WebServerDroneComm import WebserverDroneCommuncationDetails
from Cloud import Cloud
import ServerBaseStation_pb2_grpc
import grpc
from Database import Database
import asyncio
import _credentials

async def main(signal):

    communication = {}
    database = Database()
    bids = database.getBasestations()
    for i in bids:
        communication[i] = {}

    server = grpc.aio.server()
    ServerBaseStation_pb2_grpc.add_WebRtcServicer_to_server(
        WebRTCReceiver(), server)
    ServerBaseStation_pb2_grpc.add_DroneWebRtcServicer_to_server(
        DroneWebRtc(communication), server)
    ServerBaseStation_pb2_grpc.add_WebserverDroneCommuncationDetailsServicer_to_server(
        WebserverDroneCommuncationDetails(communication), server)
    ServerBaseStation_pb2_grpc.add_CloudServicer_to_server(
        Cloud(database), server
    )

    key = _credentials.SERVER_CERTIFICATE_KEY
    cert = _credentials.SERVER_CERTIFICATE
    creds = grpc.ssl_server_credentials([(key, cert)])
    listen_addr = "[::]:50051"
    server.add_secure_port(listen_addr, creds)
    print("Starting server on ", listen_addr, flush=True)
    await server.start()

    while not signal.is_set():
        await asyncio.sleep(30)
        removed = database.doCleanUp()
        print(f"Removed {str(removed)} inactive basestation(s).", flush=True)

    print("\nServer stopped here")
    await server.stop()
    # cv2.destroyAllWindows()
    # await server.wait_for_termination()

if __name__ == '__main__':
    try:
        signal = asyncio.Event()
        asyncio.run(main(signal))
    except KeyboardInterrupt:
        print("\nServer stopped")
        signal.set()