import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
from channel import Channel
import grpc
import uuid
import asyncio

class DroneWebRtc(ServerBaseStation_pb2_grpc.DroneWebRtcServicer):
    def __init__(self, communication: dict):
        self.communication = communication

    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectResponse:
        basestation_id = request.basestation_id
        stream_id = str(uuid.uuid4())
        self.communication.update({basestation_id: {stream_id:Channel(request.name)}})
        print('connect', self.communication)
        return ServerBaseStation_pb2.ConnectResponse(stream_id=stream_id)
    
    async def Stream(
        self,
        request: ServerBaseStation_pb2.StreamOffer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamAnswer:
        # offer = {'stream_id':request.stream_id,'offer':{'type':request.offer.type, 'sdp':request.offer.sdp}}
        comm = self.communication[request.basestation_id][request.stream_id]
        comm.offer = request
        while not comm.answer:
            await asyncio.sleep(0.5)

        print(comm.answer)
        # answer = ServerBaseStation_pb2.StreamAnswer(stream_id=comm.answer['stream_id'], 
        #                               answer=ServerBaseStation_pb2.StreamDesc(
        #                                   type=comm.answer['answer']['type'],
        #                                   sdp=comm.answer['answer']['sdp']),
        #                               )
        answer = comm.answer
        comm.answer = None
        print("ANNN", answer)
        return answer
    
    async def Poll(self,
        request: ServerBaseStation_pb2.PollRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.PollResponse:
        basestation_id = request.basestation_id
        stream_id = request.stream_id
        requested = False
        if self.communication[basestation_id][stream_id].requested:
            requested = True
            
        return ServerBaseStation_pb2.PollResponse(stream_needed=requested)