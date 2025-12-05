class Channel:
    def __init__(self, name):
        self.requested:bool=False
        self.offer = None
        self.answer = None
        self.name = name