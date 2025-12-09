from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer
from environment import CONFIG
from multiprocessing import Queue
import grpc
import ServerBaseStation_pb2
import ServerBaseStation_pb2_grpc
import uuid
import asyncio
from camera.IpCamera import IpCamera # REMOVE LATER WHEN CHANGING DEFAULT SOURCE
import _credentials

creds = grpc.ssl_channel_credentials(_credentials.ROOT_CERTIFICATE)

class WebRTCProducer:
    def __init__(self, basestation_id, source, stream_name="Unnamed Camera"):
        self.basestation_id = basestation_id
        self.stream_name = stream_name
        self.source = source
        self.stream_id = None
        self.pc = None
        
    async def __on_start_stream(self):
        print("Stream Starting")
        ice_server = RTCIceServer(urls='stun:stun.l.google.com:19302')
        self.pc = RTCPeerConnection(RTCConfiguration(iceServers=[ice_server]))
        
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
                
        self.pc.addTrack(self.source)
        
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        print("Setted local desc")

    async def __cleanup(self):
        print("Closing pc")
        await self.stub.Disconnect(ServerBaseStation_pb2.DisconnectRequest(stream_id=self.stream_id))
        # await self.pc.close()
        print("closing Channel")
        if hasattr(self, 'channel'):
            await self.channel.close()
    
    async def start(self, q):
        print(f"Starting producer: {self.stream_name}")
        self.q = q
        
        # await self.sio.connect(self.server_url)
        address = f"{CONFIG.get('GRPC_REMOTE_IP')}:{CONFIG.get('GRPC_REMOTE_PORT')}"

        self.channel = channel = grpc.aio.secure_channel(address, creds)
        print("some")
        self.stub = ServerBaseStation_pb2_grpc.WebRtcStub(channel)
        print("some")
        response = await self.stub.Connect(ServerBaseStation_pb2.ConnectRequest(basestation_id=self.basestation_id, name=self.stream_name))
        print("some")
        # generate session id
        self.stream_id = response.stream_id
        self.name = self.stream_name
        response = await self.stub.Register(
                        ServerBaseStation_pb2.RegisterProducerRequest(
                            basestation_id=self.basestation_id, 
                            stream_id=self.stream_id, 
                            name=self.name
                        ))
        print("some")
        await self.__on_start_stream()
        response = await self.stub.Stream(
            ServerBaseStation_pb2.StreamOffer(
                basestation_id=self.basestation_id,
                stream_id=self.stream_id, 
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
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping producer...")
        except Exception as e:
            print("EXCEPTION: ", e)
        finally:
            await self.__cleanup()