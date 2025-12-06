from DroneWebRtc import DroneWebRtc
from WebRtcReceiver import WebRTCReceiver
from WebServerDroneComm import WebserverDroneCommuncationDetails
import ServerBaseStation_pb2_grpc
import grpc




async def main(signal):

    communication = {}
    server = grpc.aio.server()
    ServerBaseStation_pb2_grpc.add_WebRtcServicer_to_server(
        WebRTCReceiverServer(), server)
    ServerBaseStation_pb2_grpc.add_DroneWebRtcServicer_to_server(
        DroneWebRtc(communication), server)
    ServerBaseStation_pb2_grpc.add_WebserverDroneCommuncationDetailsServicer_to_server(
        WebserverDroneCommuncationDetails(communication), server)
    ServerBaseStation_pb2_grpc.add_CloudServer_to_server(
        Cloud(), server
    )
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    print("Starting server on ", listen_addr)
    await server.start()

    while not signal.is_set():
        await asyncio.sleep(1)

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