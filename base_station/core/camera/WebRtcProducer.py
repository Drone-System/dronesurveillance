class WebRTCProducer:
    def __init__(self, server_url, stream_name, source=0):
        self.server_url = server_url
        self.stream_name = stream_name
        self.source = source
        self.sio = socketio.AsyncClient()
        self.stream_id = None
        self.peer_connections = {}  # viewer_sid -> RTCPeerConnection
        
        # Setup event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('producer_registered', self.on_producer_registered)
        self.sio.on('viewer_joined', self.on_viewer_joined)
        self.sio.on('answer', self.on_answer)
        self.sio.on('ice_candidate', self.on_ice_candidate)
    
    async def on_connect(self):
        print(f"Connected to server: {self.server_url}")
        await self.sio.emit('register_producer', {'name': self.stream_name})
    
    async def on_disconnect(self):
        print("Disconnected from server")
    
    async def on_producer_registered(self, data):
        self.stream_id = data['stream_id']
        print(f"Producer registered with stream ID: {self.stream_id}")
    
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