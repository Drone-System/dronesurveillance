from VideoReceiver import VideoReceiver
import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
import grpc
import uuid
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder, MediaRelay
import asyncio

class WebRTCReceiver(ServerBaseStation_pb2_grpc.WebRtcServicer):
    def __init__(self):
        self.tracks = {}
        self.producers = {}  # producer_sid -> {stream_id, name, pc}
        self.peer_connections = {}  # producer_sid -> RTCPeerConnection
        self.video_receivers = {}


    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectResponse:
        print("Connected", flush=True)
        return ServerBaseStation_pb2.ConnectResponse(stream_id=str(uuid.uuid4()))

    async def Register(
        self,
        request: ServerBaseStation_pb2.RegisterProducerRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.RegisterProducerResponse:
        print("Registered producer:", request.name)
        stream_name = request.name
        # stream_id = request.sid
        self.producers[request.stream_id] = {
            'stream_id': request.stream_id,
            'name': stream_name,
        }
        return ServerBaseStation_pb2.RegisterProducerResponse(stream_id=request.stream_id, viewer_sid='server')

    async def Stream(
        self,
        request: ServerBaseStation_pb2.StreamOffer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamAnswer:
        print("Stream Offer Received")
        stream_name = self.producers.get(request.stream_id, {}).get('name', 'Unknown')
        stream_id = self.producers.get(request.stream_id, {}).get('stream_id', request.stream_id)
        
        print(f"Received offer from producer: {stream_name}")
        offer = request.offer
        
        # Create peer connection
        pc = RTCPeerConnection()
        self.peer_connections[request.stream_id] = pc
        
        @pc.on("track")
        async def on_track(track):
            print(f"Received track: {track.kind} from {stream_name}", track.id, request.stream_id)
            
            if track.kind == "video":


                mrec = MediaRecorder(f"{track.id}.mp4", options={"framerate": "30", "video_size": "1080"})
                relay = MediaRelay()

                mrec.addTrack(relay.subscribe(track))
                video_receiver= VideoReceiver(request.basestation_id, request.stream_id,  self.producers[request.stream_id]['name']) 
                signal = asyncio.Event()
                asyncio.ensure_future(video_receiver.handle_track(relay.subscribe(track), request.stream_id, signal))
                await mrec.start()

                try:
                    self.video_receivers[request.stream_id] = (video_receiver, signal)

                except Exception as e:
                    print(f"Track ended for {stream_name}: {e}")
        @pc.on("connectionstatechange")
        async def on_connection_changed():
            print("state: ", pc.connectionState)

        # # Handle ICE candidates
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            print("received ice")
            if candidate:
                print("received", candidate)
        
        # Set remote description
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer.sdp, type=offer.type)
        )
        
        # Create and send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        

        print(pc.localDescription.type)
        print(pc.localDescription.sdp)
        return ServerBaseStation_pb2.StreamAnswer(
            stream_id=stream_id, #'server', 
            answer=ServerBaseStation_pb2.StreamDesc(
                type=pc.localDescription.type, 
                sdp=pc.localDescription.sdp
                ))
    
    async def Disconnect(
        self,
        request: ServerBaseStation_pb2.DisconnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.DisconnectResponse:
        print("Received disc")
        print(self.video_receivers)
        try:
            self.video_receivers[request.stream_id][1].set()
            self.video_receivers.pop(request.stream_id) 
        except:
            print("what the flip")
        if self.peer_connections[request.stream_id].connectionState != "closed":
            await self.peer_connections[request.stream_id].close()
        return ServerBaseStation_pb2.DisconnectResponse()