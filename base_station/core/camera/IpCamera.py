# from .Camera import Camera
import cv2

# class IpCamera(Camera):
#     def __init__(self, url):
#         super().__init__()
#         self.url = url
    
#     def connect(self):
#         self.cap = cv2.VideoCapture(self.url)

#     def recv(self) -> (bool, bytes):
#         if not self.cap.isOpened():
#             print("Error: Unable to open video stream")
#         ret, frame = self.cap.read()
#         if not ret:
#             print("Error reading")
#             return (False, None)

#         ret, buffer = cv2.imencode(".jpg", frame)
#         if not ret:
#             print("Error encoding")
#             return (False, None)

#         print(f"Doing stuff - {self.id} - {len(buffer.tobytes())}")
#         return (True, buffer.tobytes())
        
#     def disconnect(self):
#         self.cap.release()
#         self.cap = None
        
class IpCamera(VideoStreamTrack):
    """Video track that captures from webcam"""
    
    def __init__(self, connection_string=0):
        super().__init__()
        self.cap = cv2.VideoCapture(connection_string)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 24)
        
    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        ret, frame = self.cap.read()
        if not ret:
            # If camera fails, return a black frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        return video_frame
    
    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release()