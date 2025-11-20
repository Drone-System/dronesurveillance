# import cv2

# class CameraVideoTrack(VideoStreamTrack):
#     """Video track that captures from webcam"""
    
#     def __init__(self, source=0):
#         super().__init__()
#         self.cap = cv2.VideoCapture(source)
#         self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#         self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#         self.cap.set(cv2.CAP_PROP_FPS, 24)
        
#     async def recv(self):
#         pts, time_base = await self.next_timestamp()
        
#         ret, frame = self.cap.read()
#         # print("Sneding:",self.camera_id)
#         if not ret:
#             # If camera fails, return a black frame
#             frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
#         # Convert BGR to RGB
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#         # Create VideoFrame
#         video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
#         video_frame.pts = pts
#         video_frame.time_base = time_base
        
#         return video_frame
    
#     def __del__(self):
#         if hasattr(self, 'cap'):
#             self.cap.release()