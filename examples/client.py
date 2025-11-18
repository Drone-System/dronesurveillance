import asyncio
import logging

import grpc
import ServerBaseStation_pb2
import ServerBaseStation_pb2_grpc

class WebRTCProducer:
    def __init__(self, server_url, stream_name, source=0):
        self.server_url = server_url
        self.stream_name = stream_name
        self.source = source
        self.sio = socketio.AsyncClient()
        self.stream_id = None
        self.peer_connections = {}  # viewer_sid -> RTCPeerConnection
        
    
    async def on_viewer_joined(self, data):
        viewer_sid = data['viewer_sid']
        print(f"Viewer joined: {viewer_sid}")
        
        # Create new peer connection for this viewer
        pc = RTCPeerConnection()
        self.peer_connections[viewer_sid] = pc
        
        # Add video track
        video_track = CameraVideoTrack(self.source)
        pc.addTrack(video_track)
        
        # Handle ICE candidates
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                await self.sio.emit('ice_candidate', {
                    'target_sid': viewer_sid,
                    'candidate': {
                        'candidate': candidate.candidate,
                        'sdpMid': candidate.sdpMid,
                        'sdpMLineIndex': candidate.sdpMLineIndex
                    }   
                })
        
        # Create and send offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        await self.sio.emit('offer', {
            'stream_id': self.stream_id,
            'viewer_sid': viewer_sid,
            'offer': {
                'type': pc.localDescription.type,
                'sdp': pc.localDescription.sdp
            }
        })
        print(f"Sent offer to viewer {viewer_sid}")
    
    async def on_answer(self, data):
        viewer_sid = data['viewer_sid']
        answer = data['answer']
        
        if viewer_sid in self.peer_connections:
            pc = self.peer_connections[viewer_sid]
            await pc.setRemoteDescription(
                RTCSessionDescription(sdp=answer['sdp'], type=answer['type'])
            )
            print(f"Received answer from viewer {viewer_sid}")
    
    async def on_ice_candidate(self, data):
        from_sid = data['from_sid']
        candidate_data = data['candidate']
        
        if from_sid in self.peer_connections:
            pc = self.peer_connections[from_sid]
            from aiortc import RTCIceCandidate
            
            candidate = RTCIceCandidate(
                candidate=candidate_data['candidate'],
                sdpMid=candidate_data['sdpMid'],
                sdpMLineIndex=candidate_data['sdpMLineIndex']
            )
            await pc.addIceCandidate(candidate)
            print(f"Added ICE candidate from {from_sid}")
    
    async def start(self):
        print(f"Starting producer: {self.stream_name}")
        print(f"Using camera: {self.source}")
        
        await self.sio.connect(self.server_url)
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping producer...")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        # Close all peer connections
        for pc in self.peer_connections.values():
            await pc.close()
        
        await self.sio.disconnect()
        print("Producer stopped")


async def run() -> None:
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = ServerBaseStation_pb2_grpc.WebRtcStub(channel)
        response = await stub.Connect(ServerBaseStation_pb2_grpc.ConnectRequest())
        response = await stub.Register(ServerBaseStation_pb2_grpc.RegisterProducerRequest("a", "MyStream"))
        response = await stub.Register(
            ServerBaseStation_pb2_grpc.Stream(
                stream_id=response.stream_id, ))


if __name__ == "__main__":
    logging.basicConfig()
    asyncio.run(run())