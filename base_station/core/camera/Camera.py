import cv2

class Camera:
    id_tracker = 0
    def __init__(self):
        self.id = Camera.id_tracker
        Camera.id_tracker += 1
    
    def connect(self):
        pass

    def disconnect(self):
        pass

    def recv(self, frame):
        print("showing")
        cv2.imshow("Frame", frame)