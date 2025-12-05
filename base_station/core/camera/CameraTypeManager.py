from IpCamera import IpCamera


class CameraTypeManager:
    tracker_id = 0
    def __init__(self, dbManager):
        self.types = {}
        self.registerType(IpCamera, "Ip Camera")
        dbManager.updateProtocols(self.types)
        

    def registerType(cameraType: type, typeName: str):
        self.types[CameraTypeManager.tracker_id] = (cameraType, typeName)
        CameraTypeManager.tracker_id += 1

    
