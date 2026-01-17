from enum import IntEnum
from ..core import ResData, ResFileLoader
from ..common import ResDict, Buffer
from ..gx2 import GX2AttribFormat
from ..switch.memory_pool import MemoryPool


class VertexBuffer(ResData):
    """Represents a data buffer holding vertices for a Model subfile."""

    _SIGNATURE = "FVTX"

    def __init__(self):
        self.vtx_count: int
        self.gpu_buff_align = 8
        self.mempool = MemoryPool()
        self.flags: int

        self.vtx_skin_count = 0
        self.attributes: ResDict = ResDict()
        self.buffers: list[Buffer] = []

    def load(self, loader: ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        if loader.is_switch:
            from ..switch.model import VertexBufferParser

            VertexBufferParser.load(loader, self)


class VertexAttrib(ResData):
    """Represents an attribute of a VertexBuffer describing the data format,
    type and layout of a specific data subset in the buffer.
    """

    class SwitchAttribFormat(IntEnum):
        # 8 bits (8 x 1)
        FORMAT_8_UNORM = 0x00000102
        FORMAT_8_UINT = 0x00000302
        FORMAT_8_SNORM = 0x00000202
        FORMAT_8_SINT = 0x00000402
        FORMAT_8_UINTTOSINGLE = 0x00000802
        FORMAT_8_SINTTOSINGLE = 0x00000A02
        # 8 bits (4 x 2)
        FORMAT_4_4_UNORM = 0x00000001
        # 16 bits (16 x 1)
        FORMAT_16_UNORM = 0x0000010A
        FORMAT_16_UINT = 0x0000020A
        FORMAT_16_SNORM = 0x0000030A
        FORMAT_16_SINT = 0x0000040A
        FORMAT_16_SINGLE = 0x0000050A
        FORMAT_16_UINTTOSINGLE = 0x00000803
        FORMAT_16_SINTTOSINGLE = 0x00000A03
        # 16 bits (8 x 2)
        FORMAT_8_8_UNORM = 0x00000109
        FORMAT_8_8_UINT = 0x00000309
        FORMAT_8_8_SNORM = 0x00000209
        FORMAT_8_8_SINT = 0x00000409
        FORMAT_8_8_UINTTOSINGLE = 0x00000804
        FORMAT_8_8_SINTTOSINGLE = 0x00000A04
        # 32 bits (16 x 2)
        FORMAT_16_16_UNORM = 0x00000112
        FORMAT_16_16_SNORM = 0x00000212
        FORMAT_16_16_UINT = 0x00000312
        FORMAT_16_16_SINT = 0x00000412
        FORMAT_16_16_SINGLE = 0x00000512
        FORMAT_16_16_UINTTOSINGLE = 0x00000807
        FORMAT_16_16_SINTTOSINGLE = 0x00000A07
        # 32 bits (10/11 x 3)
        FORMAT_10_11_11_SINGLE = 0x00000809
        # 32 bits (8 x 4)
        FORMAT_8_8_8_8_UNORM = 0x0000010B
        FORMAT_8_8_8_8_SNORM = 0x0000020B
        FORMAT_8_8_8_8_UINT = 0x0000030B
        FORMAT_8_8_8_8_SINT = 0x0000040B
        FORMAT_8_8_8_8_UINTTOSINGLE = 0x0000080B
        FORMAT_8_8_8_8_SINTTOSINGLE = 0x00000A0B
        # 32 bits (10 x 3 + 2)
        FORMAT_10_10_10_2_UNORM = 0x0000000B
        FORMAT_10_10_10_2_UINT = 0x0000090B
        FORMAT_10_10_10_2_SNORM = 0x0000020E  # High 2 bits are UNorm
        FORMAT_10_10_10_2_SINT = 0x0000099B
        # 64 bits (16 x 4)
        FORMAT_16_16_16_16_UNORM = 0x00000115
        FORMAT_16_16_16_16_SNORM = 0x00000215
        FORMAT_16_16_16_16_UINT = 0x00000315
        FORMAT_16_16_16_16_SINT = 0x00000415
        FORMAT_16_16_16_16_SINGLE = 0x00000515
        FORMAT_16_16_16_16_UINTTOSINGLE = 0x0000080E
        FORMAT_16_16_16_16_SINTTOSINGLE = 0x00000A0E
        # 32 bits (32 x 1)
        FORMAT_32_UINT = 0x00000314
        FORMAT_32_SINT = 0x00000416
        FORMAT_32_SINGLE = 0x00000516
        # 64 bits (32 x 2)
        FORMAT_32_32_UINT = 0x00000317
        FORMAT_32_32_SINT = 0x00000417
        FORMAT_32_32_SINGLE = 0x00000517
        # 96 bits (32 x 3)
        FORMAT_32_32_32_UINT = 0x00000318
        FORMAT_32_32_32_SINT = 0x00000418
        FORMAT_32_32_32_SINGLE = 0x00000518
        # 128 bits (32 x 4)
        FORMAT_32_32_32_32_UINT = 0x00000319
        FORMAT_32_32_32_32_SINT = 0x00000419
        FORMAT_32_32_32_32_SINGLE = 0x00000519

    def __init__(self):
        self.name = ""
        self.buffer_idx = 0
        self.offset = 0
        self.format_ = GX2AttribFormat.FORMAT_32_32_32_SINGLE

    def __repr__(self):
        return "VertexAttrib{" + str(self.name) + "}"

    def load(self, loader: ResFileLoader):
        if loader.is_switch:
            self.name = loader.load_string()
            loader.endianness = ">"
            self.format_ = self.__convert_to_gx2(self.SwitchAttribFormat(loader.read_uint16()))
            loader.endianness = "<"
            loader.seek(2)
            self.offset = loader.read_uint16()
            self.buffer_idx = loader.read_uint16()

    def __convert_to_gx2(self, att: "SwitchAttribFormat"):
        return GX2AttribFormat[att.name]
