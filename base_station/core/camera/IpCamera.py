from .Camera import Camera
import cv2

class IpCamera(Camera):
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def connect(self):
        self.cap = cv2.VideoCapture(self.url)

    def recv(self) -> (bool, bytes):
        if not self.cap.isOpened():
            print("Error: Unable to open video stream")
        ret, frame = self.cap.read()
        if not ret:
            print("Error reading")
            return (False, None)

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            print("Error encoding")
            return (False, None)

        print(f"Doing stuff - {self.id} - {len(buffer.tobytes())}")
        return (True, buffer.tobytes())
        
    def disconnect(self):
        self.cap.release()
        self.cap = None
        
