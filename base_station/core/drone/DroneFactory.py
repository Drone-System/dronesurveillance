from drone.Drone import IDrone
from drone.DjiTello import DjiTelloDrone

class DroneFactory:

    def newDrone(drone_type: str, config: dict)-> IDrone:

        if drone_type == "dji_tello_drone":
            return DjiTelloDrone()