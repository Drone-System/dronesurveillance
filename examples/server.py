import asyncio
import logging

import grpc
import ServerBaseStation_pb2
import ServerBaseStation_pb2_grpc


class WebRtcProducer(ServerBaseStation_pb2_grpc.WebRtcServicer):
    def __init__(self, sid):
        self.ola = sid
    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectResponse:
        print("Connection established:", request.session_id, self.ola)
        return ServerBaseStation_pb2.ConnectResponse()

    async def Register(
        self,
        request: ServerBaseStation_pb2.RegisterProducerRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.RegisterProducerResponse:
        print("Registered producer:", request.name)
        return ServerBaseStation_pb2.RegisterProducerResponse()

    async def Stream(
        self,
        request: ServerBaseStation_pb2.StreamOffer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamAnswer:
        print("Stream Offer Received")
        #TODO
        return ServerBaseStation_pb2.StreamAnswer()


async def serve() -> None:
    server = grpc.aio.server()
    ServerBaseStation_pb2_grpc.add_WebRtcServicer_to_server(WebRtcProducer("ola"), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    # print(server.ola)
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())