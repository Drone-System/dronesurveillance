from drone.Drone import IDrone
from djitellopy import Tello
from aiortc import VideoStreamTrack
from av import VideoFrame

class Movement:
    def __init__(self, back_front, left_rigth, down_up, yaw):
        self.back_front = back_front
        self.left_rigth = left_rigth
        self.down_up = down_up
        self.yaw = yaw

    def setBackFront(self, n):
        self.back_front = n
    def setLeftRight(self, n):
        self.left_rigth = n
    def setDownUp(self, n):
        self.down_up = n
    def setYaw(self, n):
        self.yaw = n


class DjiTelloVideoTrack(VideoStreamTrack):
    def __init__(self, drone):
        super().__init__()
        self.drone = drone
        self.drone.streamon()
        self.frame_read = self.drone.get_frame_read()

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = self.frame_read.frame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame



class DjiTelloDrone(IDrone):
    
    UNIT = 50

    def __init__(self, ip="0.0.0.0"): #, ip, port, video_port):
        # self.ip = ip
        # self.port = port
        # self.video_port = video_port
        super().__init__()
        self.drone = Tello()
        self.movement = Movement(0,0,0,0)
        self.video_track = VideoStreamTrack
        self.isFlying = False

    
    def connect(self):
        self.drone.connect()
        self.video_track = DjiTelloVideoTrack(self.drone)

    def disconnect(self):
        self.drone.disconnect()

    def moveBack(self, move:bool = True):
        self.movement.setBackFront(-UNIT if move else 0)
    def moveFront(self, move:bool = True):
        self.movement.setBackFront(UNIT if move else 0)

    def moveLeft(self, move:bool = True):
        self.movement.setLeftRight(-UNIT if move else 0)
    def moveRight(self, move:bool = True):
        self.movement.setLeftRight(UNIT if move else 0)

    def moveDown(self, move:bool = True):
        self.movement.setDownUp(-UNIT if move else 0)
    def moveUp(self, move:bool = True):
        self.movement.setDownUp(UNIT if move else 0)

    def rotateLeft(self, move:bool = True):
        self.movement.setYaw(-UNIT if move else 0)
    def rotateRight(self, move:bool = True):
        self.movement.setYaw(UNIT if move else 0)

    def takeoff(self):
        if not self.isFlying:
            self.isFlying = True
            self.drone.takeoff()
    
    def land(self):
        if self.isFlying:
            self.isFlying = False
            self.drone.land()
    
    def isFlying(self):
        return self.isFlying

    def sendCommand(self):
        if self.isFlying:
            self.drone.send_rc_control(self.movement.left_rigth, 
                                    self.movement.back_front, 
                                    self.movement.down_up, 
                                    self.movement.yaw)

    def getVideoTrack(self):
        return self.video_track