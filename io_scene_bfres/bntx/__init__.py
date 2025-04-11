import io
import logging

from io_scene_bfres.bfrespy import core

from .nx import NX

log = logging.getLogger(__name__)


class BNTX(core.ResData):
    """BNTX texture pack."""

    __signature = "BNTX"

    def __init__(self, stream: io.BytesIO):
        from io_scene_bfres.bfrespy.switch.switchcore import ResFileSwitchLoader

        with ResFileSwitchLoader(self, stream) as loader:
            self.load(loader)

    def load(self, loader: core.ResFileLoader):
        # Header
        loader._check_signature(self.__signature)
        loader.seek(4)
        self.version = loader.read_uint32()
        self.endianness = loader._read_byte_order()
        self.alignment = loader.read_byte()
        self.target_addr_size = loader.read_byte()
        offset_to_filename = loader.read_uint32()
        self.flags = loader.read_uint16()
        self.block_offs = loader.read_uint16()
        relocation_table_offs = loader.read_uint32()
        siz_file = loader.read_uint32()

        self.nx = loader.load(NX, use_offset=False)
