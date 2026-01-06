from . import core


class TextureShared(core.ResData):
    """Represents an FMDL subfile in a ResFile storing multi-dimensional 
    texture data.
    """

    def __init__(self):
        self.name: str
        self.path: str
        self.width: int
        self.height: int
        self.depth: int
        self.mipcount: int
        self.array_length: int
        self.userdata: 'UserData'

    def __repr__(self):
        return "TextureShared{" + str(self.name) + "}"

    def get_swizzled_data(self, arraylevel=None, miplevel=None):
        return None

    def load(self, loader: core.ResData):
        pass
