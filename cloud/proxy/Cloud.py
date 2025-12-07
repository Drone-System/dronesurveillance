import ServerBaseStation_pb2_grpc, ServerBaseStation_pb2
import uuid
import grpc

class Cloud(ServerBaseStation_pb2_grpc.CloudServicer):

    def __init__(self, db):
        self.db = db

    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectToCloudRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectToCloudResponse:
        # register in database
        print("Received connection request from db", request.name)
        bs_id = self.db.registerBasestation(request.name, request.password)
        return ServerBaseStation_pb2.ConnectToCloudResponse(id=bs_id)
    
    async def Ping(
        self,
        request: ServerBaseStation_pb2.PingRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.PingResponse:
        self.db.updateTime(request.id)
        return ServerBaseStation_pb2.PingResponse()
