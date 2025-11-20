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

class WebRTCProducer:
    def __init__(self, basestation_id, source, stream_name="Unnamed Camera"):
        self.basestation_id = basestation_id
        self.stream_name = stream_name
        self.source = source
        self.stream_id = None
        # self.pc = RTCPeerConnection()  # Only one peer connection per camera
        
    async def __on_start_stream(self):
        print("Stream Starting")
        self.pc = RTCPeerConnection()
        
        # Handle ICE candidates
        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            # print("Hello"+ candidate)
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
                
        # Add video track
        # video_track = CameraVideoTrack(self.camera_id)
        
        # self.pc.addTrack(video_track)
        # self.source = MediaPlayer("/dev/video2")
        self.pc.addTrack(self.source)
        
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        print("Setted local desc")

    async def __cleanup(self):
        print("Closing pc")
        await self.pc.close()
        print("closing Channel")
        if hasattr(self, 'channel'):
            await self.channel.close()
    
    async def start(self, q: Queue):
        print(f"Starting producer: {self.stream_name}")
        self.q = q
        
        # await self.sio.connect(self.server_url)
        address = f"{CONFIG.get("GRPC_REMOTE_IP")}:{CONFIG.get("GRPC_REMOTE_PORT")}"
        self.channel = channel = grpc.aio.insecure_channel(address)

        self.stub = ServerBaseStation_pb2_grpc.WebRtcStub(channel)
        response = await self.stub.Connect(ServerBaseStation_pb2.ConnectRequest())

        # generate session id
        sid = str(uuid.uuid4())
        name = f"{self.basestation_id}/{sid}"
        response = await self.stub.Register(ServerBaseStation_pb2.RegisterProducerRequest(sid=sid, name=name))

        await self.__on_start_stream()
        response = await self.stub.Stream(
            ServerBaseStation_pb2.StreamOffer(
                sid=sid,
                stream_id=response.stream_id, 
                viewer_sid=response.viewer_sid, 
                offer=ServerBaseStation_pb2.StreamDesc(
                    type=self.pc.localDescription.type,
                    sdp=self.pc.localDescription.sdp)))

        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=response.answer.sdp, type=response.answer.type)
        )
        # Keep running
        try:
            while True:
                # CHECK KEEP Alive
                if not q.empty():
                    print("QUEUE NOT")
                    message = q.get_nowait()
                    if message == 1:
                        await self.__cleanup()
                        exit(0)
                else:
                    print("EMTPY")
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping producer...")
        except Exception as e:
            print("EXCEPTION: ", e)
        finally:
            await self.__cleanup()