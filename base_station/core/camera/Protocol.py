from .IpCamera import IpCamera

def cameraTypeTranslator(id: int) -> type:
    if id == 0:
        return IpCamera