from ..core import ResData, ResFileLoader


class MemoryPool(ResData):
    """Represents a buffer info section."""
    __SIZE = 288

    def __init__(self):
        pool_array = bytes()

    def load(self, loader):
        pass
        # nothing?


class BufferSize(ResData):
    """Represents a buffer info section."""

    def __init__(self):
        self.size: int
        self.flags: int

    def load(self, loader: ResFileLoader):
        self.size = loader.read_uint32()
        self.flags = loader.read_uint32()
        loader.seek(40)


class BufferInfo(ResData):
    """Represents an buffer info section in a ResFile subfile. References 
    vertex and index buffers.
    """
    # Public Properties
    buff_offs: int
    vtx_buffer_data: list[bytes] = []
    index_buffer_data: list[bytes] = []
    unk = 34

    def load(self, loader: ResFileLoader):
        BufferInfo.unk = loader.read_uint32()
        size = loader.read_uint32()
        BufferInfo.buff_offs = loader.read_int64()
        padding = loader.read_bytes(16)
