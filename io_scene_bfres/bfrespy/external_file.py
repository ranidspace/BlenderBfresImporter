import io
from . import core


class ExternalFile(core.ResData):
    """Represents a file attachment to a ResFile which can be of arbitrary 
    data.
    """

    def __init__(self):
        self.data: bytes
        self.loaded_file_data: object

    def get_stream(self, writeable=False):
        """Opens and returns a BytesIO on the raw data byte array, which 
        optionally can be written to.
        """
        return io.BytesIO(self.data)

    def load(self, loader: core.ResFileLoader):
        offs_data = loader.read_offset()
        siz_data = loader.read_size()
        self.data = loader.load_custom(
            bytes, lambda: loader.read_bytes(siz_data), offset=offs_data
        )
