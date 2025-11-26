
class IDrone:

    def __init__(self):
        pass

    def connect(self):
        raise Exception("Not implemented")

    def disconnect(self):
        raise Exception("Not implemented")

    def moveFront(self):
        raise Exception("Not implemented")

    def moveBack(self):
        raise Exception("Not implemented")

    def moveLeft(self):
        raise Exception("Not implemented")

    def moveRight(self):
        raise Exception("Not implemented")

    def rotateLeft(self):
        raise Exception("Not implemented")
    
    def rotateRight(self):
        raise Exception("Not implemented")

    def sendCommand(self):
        raise Exception("Not implemented")

    def getVideoTrack(self):
        raise Exception("Not implemented")
    
    def isFlying(self):
        raise Exception("Not implemented")

    def decode(self, string:str):
        keys = " ".split(string)
        move = True
        if (keys[0] == "stop"):
            move = False
            keys.pop(0)
        k = keys[0]
        if k == 'w':
            self.moveFront(move)
        if k == 'a':
            self.moveLeft(move)
        if k == 's':
            self.moveBack(move)
        if k == 'd':
            self.moveRight(move)
        if k == 'q':
            self.rotateLeft(move)
        if k == 'e':
            self.rotateRight(move)
        if k == 'space':
            if not self.isFlying():
                self.takeoff()
            else:
                self.land()
