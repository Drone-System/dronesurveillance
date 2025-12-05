import ServerBaseStation_pb2_grpc, ServerBaseStation_pb2
import uuid

class Cloud(ServerBaseStation_pb2_grpc.CloudServicer):

    def __init__(self):
        pass
    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectToCloudRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectToCloudResponse:
        name = request.name
        bs_id = str(uuid.uuid4)

        # register in database

        return ServerBaseStation_pb2.ConnectToCloudResponse(id=bs_id)