from av import VideoFrame
import base64
import asyncio
import redis
from datetime import datetime
import time
import cv2

class VideoReceiver:
    def __init__(self, stream_id, name):
        self.track = None
        self.running = True
        self.stream_id = stream_id.replace("/", "_") + "_" + name
        # self.name = name
        try:
            self.r = redis.Redis(host='red', port=6379, db=0, socket_connect_timeout=5)
            self.r.ping()  # Test connection
            print("Connected to Redis successfully!")
        except redis.ConnectionError as e:
            print(f"ERROR: Cannot connect to Redis server at localhost:6379")

    async def handle_track(self, track, name="Frame", signal: asyncio.Event = None):
        print("Inside handle track")
        self.track = track
        frame_count = 0
        count = 0
        self.signal = signal
        print(self.stream_id)
        while not self.signal.is_set():
            await asyncio.sleep(0.001)
            try:
                # print("Waiting for frame...")
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                frame_count += 1
                # print(f"Received frame {frame_count}")
                
                if isinstance(frame, VideoFrame):
                    # print(f"Frame type: VideoFrame, pts: {frame.pts}, time_base: {frame.time_base}")
                    frame = frame.to_ndarray(format="bgr24")
                elif isinstance(frame, np.ndarray):
                    print(f"Frame type: numpy array")
                else:
                    print(f"Unexpected frame type: {type(frame)}")
                    continue
                current_time = datetime.now()
                new_time = current_time # - timedelta( seconds=55)
                timestamp = new_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                cv2.putText(frame, timestamp, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
                # Convert to base64 string for Redis
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                # Publish to Redis channel
                self.r.publish(self.stream_id, jpg_as_text)
                
                # Also store latest frame in a key (for late joiners)
                # self.r.set(f'latest_frame_{self.stream_id}', jpg_as_text)
                # Store latest frame with expiration (5 seconds)
                self.r.setex("latest_frame_"+self.stream_id, 5, jpg_as_text)
                
                # Set heartbeat with expiration (5 seconds)
                self.r.setex("heartbeat_"+self.stream_id, 5, str(int(time.time())))
                #  # Add timestamp to the frame
                # print(f"Saved frame {frame_count} to file")
                # cv2.imshow(name, frame)
    
                # Exit on 'q' key press
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
                # count = 0
            except asyncio.TimeoutError:
                print("Timeout waiting for frame, continuing...")
            except Exception as e:
                print(f"Error in handle_track: {str(e)}")
                if "Connection" in str(e):
                    break
        print("Exiting handle_track")

    def exit(self):
        print("Setted running false")
        self.running = False