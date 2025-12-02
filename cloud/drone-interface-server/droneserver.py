import grpc
import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
import uuid
import asyncio

class Channel:
    def __init__(self, name):
        self.requested:bool=False
        self.offer = None
        self.answer = None
        self.name = name

class DroneWebRtc(ServerBaseStation_pb2_grpc.DroneWebRtcServicer):
    def __init__(self, communication):
        self.communication = communication

    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectResponse:
        basestation_id = request.basestation_id
        stream_id = f"{basestation_id}/{str(uuid.uuid4())}"
        self.communication.update({stream_id:Channel(request.name)})
        print('connect')
        return ServerBaseStation_pb2.ConnectResponse(stream_id=stream_id, )
    
    async def Stream(
        self,
        request: ServerBaseStation_pb2.StreamOffer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamAnswer:
        offer = {'stream_id':request.stream_id,'offer':{'type':request.offer.type, 'sdp':request.offer.sdp}}
        comm = self.communication[request.stream_id]
        comm.offer = request
        while not comm.answer:
            await asyncio.sleep(0.5)

        print(comm.answer)
        answer = ServerBaseStation_pb2.StreamAnswer(stream_id=comm.answer['stream_id'], 
                                      answer=ServerBaseStation_pb2.StreamDesc(
                                          type=comm.answer['answer']['type'],
                                          sdp=comm.answer['answer']['sdp']),
                                      )
        comm.answer = None
        return answer
    

class WebserverDroneCommuncationDetails(ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsServicer):
    def __init__(self, communication):
        self.communication = communication

    async def RequestDroneStream(
        self,
        request: ServerBaseStation_pb2.DroneStreamRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.DroneStreamRequest:
        basestation_id = ServerBaseStation_pb2.DroneStreamRequest.baseStation_id
        drone_id = ServerBaseStation_pb2.DroneStreamRequest.drone_id
        channel = self.communication[basestation_id][drone_id]
        channel.requested = True
        while channel.offer is None:
            await asyncio.sleep(0.5)
        print('connect')
        return channel.offer
    
    async def Answer(
        self,
        request: ServerBaseStation_pb2.StreamAnswer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.Ack:
        self.communication[request.stream_id].answer = request
        return ServerBaseStation_pb2.Ack()
    
    async def RequestAvailableDrones(
        self,
        request: ServerBaseStation_pb2.AvailableDroneRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.AvailableDronesResponse:
        stream_ids = []
        for stream_id in self.communication.keys():
            if stream_id.split("/")[0] == request.info.id:
                name = self.communication[stream_id].name
                stream_ids.append(ServerBaseStation_pb2.DroneInfo(id=stream_id, name=name))
        return ServerBaseStation_pb2.AvailableDronesResponse(stream_ids)    

async def main():
    communication = {}
    server = grpc.aio.server()
    ServerBaseStation_pb2_grpc.add_DroneWebRtcServicer_to_server(DroneWebRtc(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    print("Starting server on ", listen_addr)
    await server.start()
    #asyncio.ensure_future(app.run('0.0.0.0', port=443, ssl_context=context, debug=False, use_reloader=False))
    #app.run('0.0.0.0', port=443, ssl_context=context, debug=True)
    await server.wait_for_termination()