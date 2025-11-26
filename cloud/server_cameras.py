import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaRecorder, MediaRelay
from av import VideoFrame

import uuid

import argparse
import threading
from time import sleep
import ServerBaseStation_pb2_grpc
import ServerBaseStation_pb2
import grpc
import logging
import fractions
from datetime import datetime,timedelta

class VideoReceiver:
    def __init__(self):
        self.track = None
        self.running = True

    async def handle_track(self, track, name="Frame", signal: asyncio.Event = None):
        print("Inside handle track")
        self.track = track
        frame_count = 0
        count = 0
        self.signal = signal
        while not self.signal.is_set():
            await asyncio.sleep(0.001)
            try:
                # print("Waiting for frame...")
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                frame_count += 1
                print(f"Received frame {frame_count}")
                
                if isinstance(frame, VideoFrame):
                    print(f"Frame type: VideoFrame, pts: {frame.pts}, time_base: {frame.time_base}")
                    frame = frame.to_ndarray(format="bgr24")
                elif isinstance(frame, np.ndarray):
                    print(f"Frame type: numpy array")
                else:
                    print(f"Unexpected frame type: {type(frame)}")
                    continue
                
                 # Add timestamp to the frame
                current_time = datetime.now()
                new_time = current_time # - timedelta( seconds=55)
                timestamp = new_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                cv2.putText(frame, timestamp, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.imwrite(f"imgs/received_frame_{frame_count}.jpg", frame)
                print(f"Saved frame {frame_count} to file")
                cv2.imshow(name, frame)
    
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                count = 0
            except asyncio.TimeoutError:
                print("Timeout waiting for frame, continuing...")
            except Exception as e:
                # print(f"Error in handle_track: {str(e)}")
                if "Connection" in str(e):
                    break
                count += 1
                # print(count)
                # if count >= 2000: # break after 2000
                #     break
        print("Exiting handle_track")

    def exit(self):
        print("Setted running false")
        self.running = False

class WebRTCReceiverServer(ServerBaseStation_pb2_grpc.WebRtcServicer):
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
        return ServerBaseStation_pb2.ConnectResponse(stream_id=uuid.uuid4())

    async def Register(
        self,
        request: ServerBaseStation_pb2.RegisterProducerRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.RegisterProducerResponse:
        print("Registered producer:", request.name)
        stream_name = request.name
        stream_id = f"stream_{request.sid}"
        self.producers[request.sid] = {
            'stream_id': stream_id,
            'name': stream_name,
            'sid': request.sid
        }
        return ServerBaseStation_pb2.RegisterProducerResponse(stream_id=stream_id, viewer_sid='server')

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


                mrec = MediaRecorder(f"{track.id}.mp4", options={"framerate": "30", "video_size": "640x480"})
                relay = MediaRelay()

                mrec.addTrack(relay.subscribe(track))
                video_receiver= VideoReceiver() 
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
        # @pc.on("icecandidate")
        # async def on_icecandidate(candidate):
        #     if candidate:
        #         await self.sio.emit('ice_candidate', {
        #             'from_sid': 'server',
        #             'candidate': {
        #                 'candidate': candidate.candidate,
        #                 'sdpMid': candidate.sdpMid,
        #                 'sdpMLineIndex': candidate.sdpMLineIndex
        #             }
        #         }, room=sid)
        
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


async def main(signal):

    server = grpc.aio.server()
    ServerBaseStation_pb2_grpc.add_WebRtcServicer_to_server(WebRTCReceiverServer(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    print("Starting server on ", listen_addr)
    await server.start()

    while not signal.is_set():
        await asyncio.sleep(1)

    print("\nServer stopped here")
    await server.stop()
    # cv2.destroyAllWindows()
    # await server.wait_for_termination()

if __name__ == '__main__':
    try:
        signal = asyncio.Event()
        asyncio.run(main(signal))
    except KeyboardInterrupt:
        print("\nServer stopped")
        signal.set()
        cv2.destroyAllWindows()