from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from environment import CONFIG
from multiprocessing import Queue
import grpc
import ServerBaseStation_pb2
import ServerBaseStation_pb2_grpc
import uuid
import asyncio
from camera.IpCamera import IpCamera # REMOVE LATER WHEN CHANGING DEFAULT SOURCE

class DroneWebRTCProducer:
    def __init__(self, basestation_id, source, stream_name="Unnamed Drone"):
        self.basestation_id = basestation_id
        self.stream_name = stream_name
        self.source = source
        self.stream_id = None
        # self.pc = RTCPeerConnection()  # Only one peer connection per camera
        
    async def __on_start_stream(self):
        print("Stream Starting")
        self.pc = RTCPeerConnection()
        self.source.connect()
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

        @self.pc.on("connectionstatechange")
        async def on_connection_changed():
            print("state: ", self.pc.connectionState)

        channel = self.pc.createDataChannel("commands")

        @channel.on("message")
        async def on_message(message):
            print("message", message)
            self.source.decode(message)

        
        self.pc.addTrack(self.source.getVideoTrack())
        
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        print("Setted local desc")

    async def __cleanup(self):
        print("Closing pc")
        await self.stub.Disconnect(ServerBaseStation_pb2.DisconnectRequest(stream_id=self.sid))
        # await self.pc.close()
        print("closing Channel")
        if hasattr(self, 'channel'):
            await self.channel.close()
    
    async def start(self, q):
        print(f"Starting drone producer: {self.stream_name}")
        self.q = q
        
        # await self.sio.connect(self.server_url)
        address = f"{CONFIG.get('GRPC_REMOTE_IP')}:{CONFIG.get('GRPC_REMOTE_PORT')}"
        self.channel = channel = grpc.aio.insecure_channel(address)
        self.stub = ServerBaseStation_pb2_grpc.DroneWebRtcStub(channel)
        response = await self.stub.Connect(ServerBaseStation_pb2.ConnectRequest(basestation_id=self.basestation_id, name= "test"))
        print("connected")
        self.sid = response.stream_id
        response = False
        while not response:
            response = await self.stub.Poll(ServerBaseStation_pb2.PollRequest(basestation_id=self.basestation_id, stream_id=self.sid))
            response = response.stream_needed
            print("polled", response)
            await asyncio.sleep(0.5)
        print("some")
        # generate session id
        # self.sid = str(uuid.uuid4())
        # response = await self.stub.Register(ServerBaseStation_pb2.RegisterProducerRequest(sid=self.sid, name=self.name))
        print("some")
        await self.__on_start_stream()
        response = await self.stub.Stream(
            ServerBaseStation_pb2.StreamOffer(
                basestation_id=self.basestation_id,
                stream_id=self.sid, 
                offer=ServerBaseStation_pb2.StreamDesc(
                    type=self.pc.localDescription.type,
                    sdp=self.pc.localDescription.sdp)))

        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=response.answer.sdp, type=response.answer.type)
        )
        print("Setted Remote")
        # Keep running
        try:
            while not self.q.is_set():
                self.source.sendCommand()
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping producer...")
        except Exception as e:
            print("EXCEPTION: ", e)
        finally:
            await self.__cleanup()