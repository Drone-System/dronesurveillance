import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
from channel import Channel
import grpc
import asyncio

class WebserverDroneCommuncationDetails(ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsServicer):
    def __init__(self, communication: dict):
        self.communication = communication

    async def RequestDroneStream(
        self,
        request: ServerBaseStation_pb2.DroneStreamRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamOffer:
        basestation_id = request.basestation_id
        drone_id = request.drone_id
        channel = self.communication[basestation_id][drone_id]
        channel.requested = True
        while channel.offer is None:
            await asyncio.sleep(0.5)
        print('connect', channel.offer)
        return channel.offer
    
    async def Answer(
        self,
        request: ServerBaseStation_pb2.StreamAnswer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.Ack:
        self.communication[request.basestation_id][request.stream_id].answer = request
        return ServerBaseStation_pb2.Ack()
    
    async def RequestAvailableDrones(
        self,
        request: ServerBaseStation_pb2.AvailableDroneRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.AvailableDronesResponse:
        stream_ids = []
        if request.basestation_id in self.communication:
            for stream_id in self.communication[request.basestation_id].keys():
                name = self.communication[request.basestation_id][stream_id].name
                stream_ids.append(ServerBaseStation_pb2.DroneInfo(id=stream_id, name=name))
        return ServerBaseStation_pb2.AvailableDronesResponse(info=stream_ids)