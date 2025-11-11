from camera.CameraManager import CameraManager
from camera.IpCamera import IpCamera


def main():
    manager = CameraManager(0, "MyBaseStation")
    # cam = IpCamera("udp://localhost:5000")
    cam = IpCamera("udp://192.168.10.1:11111")
    cam2 = IpCamera(0)
    # cam2 = IpCamera("udp://192.168.10.1:11111")
    manager.registerCamera(cam)
    manager.registerCamera(cam2)
    manager.processCameras()
    # count = 0
    # while count < 20000:
    #     manager.processCameras()
    #     count +=1

    manager.removeCamera(cam2)
    manager.removeCamera(cam)

if __name__ == "__main__":
    main()