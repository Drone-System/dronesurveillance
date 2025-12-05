from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from environment import CONFIG
from multiprocessing import Queue
import grpc
import ServerBaseStation_pb2
import ServerBaseStation_pb2_grpc
import uuid
import asyncio


class WebRtcDrone(ServerBaseStation_pb2_grpc.DroneWebRtc):
    def __init__(self, basestation_id, source, drone_name="Unnamed Drone"):
        self.basestation_id = basestation_id
        self.stream_name = stream_name
        self.source = source

    async def RequestStream(
        self,
        request: ServerBaseStation_pb2.StreamRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamOffer:
        print("Stream request Received")
        return await self.__on_start_stream()

    
    async def Answer(
        self,
        request: ServerBaseStation_pb2.StreamAnswer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectResponse:
        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=request.answer.sdp, type=request.answer.type)
        )
        print("Remote Description Setted.")
        return ServerBaseStation_pb2.ConnectResponse

    async def Disconnect(
        self,
        request: ServerBaseStation_pb2.DisconnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.DisconnectResponse:
        await self.__cleanup()
        return ServerBaseStation_pb2.DisconnectResponse()



    async def __on_start_stream(self) -> ServerBaseStation_pb2.StreamOffer:
        print("Stream Starting")
        self.pc = RTCPeerConnection()
        self.pc.addTrack(self.source)
        
        # Handle ICE candidates
        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            print("In ice")
            if candidate:
                response = await self.stub.IceCandidateRequest(
                    candidate=candidate.candidate, 
                    sdpMid=candidate.sdpMid,
                    sdpMLineIndex=candidate.sdpMLineIndex
                )

                candidate = RTCIceCandidate(
                    candidate=response.candidate, 
                    sdpMid=response.sdpMid,
                    sdpMLineIndex=response.sdpMLineIndex
                )
                await pc.addIceCandidate(candidate)
                
        
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        print("Setted local desc")

        return ServerBaseStation_pb2.StreamOffer(stream_id=self.sid, 
                                                    offer=ServerBaseStation_pb2.StreamDesc(
                                                        type=self.pc.localDescription.type, 
                                                        sdp=self.pc.localDescription.sdp))

    async def __cleanup(self):
        print("Closing pc")
        await self.pc.close()
    

class Drone:
    def __init__(self, basestation_id, source, stream_name="Unnamed Drone"):
        self.basestation_id = basestation_id
        self.stream_name = stream_name
        self.source = source
        self.stream_id = None
        # self.pc = RTCPeerConnection()  # Only one peer connection per drone
        
    # async def __on_start_stream(self):
    #     print("Stream Starting")
    #     self.pc = RTCPeerConnection()
        
    #     # Handle ICE candidates
    #     @self.pc.on("icecandidate")
    #     async def on_icecandidate(candidate):
    #         print("In ice")
    #         if candidate:
    #             response = await self.stub.IceCandidateRequest(
    #                 candidate=candidate.candidate, 
    #                 sdpMid=candidate.sdpMid,
    #                 sdpMLineIndex=candidate.sdpMLineIndex
    #             )

    #             candidate = RTCIceCandidate(
    #                 candidate=response.candidate, 
    #                 sdpMid=response.sdpMid,
    #                 sdpMLineIndex=response.sdpMLineIndex
    #             )
    #             await pc.addIceCandidate(candidate)
                
    #     self.pc.addTrack(self.source)
        
    #     offer = await self.pc.createOffer()
    #     await self.pc.setLocalDescription(offer)
    #     print("Setted local desc")

    
    async def start(self, q, port: int):

        server = grpc.aio.server()
        ServerBaseStation_pb2_grpc.add_WebRtcServicer_to_server(
            WebRtcDrone(self.basestation_id, self.source, self.drone_name), 
            server
        )
            
        listen_addr = f"[::]:{str(port)}"
        server.add_insecure_port(listen_addr)
        print("Starting server on ", listen_addr)
        await server.start()

        await server.wait_for_termination()

        # print(f"Starting producer: {self.stream_name}")
        # self.q = q
        
        # # await self.sio.connect(self.server_url)
        # address = f"{CONFIG.get('GRPC_REMOTE_IP')}:{CONFIG.get('GRPC_REMOTE_PORT')}"
        # self.channel = channel = grpc.aio.insecure_channel(address)
        # print("some")
        # self.stub = ServerBaseStation_pb2_grpc.WebRtcStub(channel)
        # print("some")
        # response = await self.stub.Connect(ServerBaseStation_pb2.ConnectRequest())
        # print("some")
        # # generate session id
        # self.sid = str(uuid.uuid4())
        # self.name = f"{self.basestation_id}/{self.sid}"
        # response = await self.stub.Register(ServerBaseStation_pb2.RegisterProducerRequest(sid=self.sid, name=self.name))
        # print("some")
        # await self.__on_start_stream()
        # response = await self.stub.Stream(
        #     ServerBaseStation_pb2.StreamOffer(
        #         stream_id=self.sid, 
        #         offer=ServerBaseStation_pb2.StreamDesc(
        #             type=self.pc.localDescription.type,
        #             sdp=self.pc.localDescription.sdp)))

        # await self.pc.setRemoteDescription(
        #     RTCSessionDescription(sdp=response.answer.sdp, type=response.answer.type)
        # )
        # print("Setted Remote")
        # # Keep running
        # try:
        #     while not self.q.is_set():
        #         await asyncio.sleep(1)
        # except KeyboardInterrupt:
        #     print("\nStopping producer...")
        # except Exception as e:
        #     print("EXCEPTION: ", e)
        # finally:
        #     await self.__cleanup()