from camera.CameraManager import CameraManager
from camera.IpCamera import IpCamera


def main():
    manager = CameraManager(0, "MyBaseStation")
    cam = IpCamera("udp://localhost:5000")
    cam2 = IpCamera(2)
    # manager.registerCamera(cam2)
    manager.registerCamera(cam)
    count = 0
    while count < 20000:
        manager.processCameras()
        count +=1

    manager.removeCamera(cam)
    # manager.removeCamera(cam2)

if __name__ == "__main__":
    main()