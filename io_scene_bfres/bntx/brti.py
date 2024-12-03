from .pixelfmt.formatinfo import formats, bpps, blk_dims
from .pixelfmt.swizzle import deswizzle, div_round_up, pow2_round_up
from .pixelfmt import TextureFormat
from enum import IntEnum
from ..bfrespy import core
import logging
import io
log = logging.getLogger(__name__)


class BRTI(core.ResData):
    """A BRTI in a BNTX."""
    __signature = 'BRTI'

    def __init__(self):
        self.name: str
        self.mip_offsets = []
        self.mip_data: bytes

    def load(self, loader: core.ResFileLoader):
        loader._check_signature(self.__signature)
        length = loader.read_uint32()
        length1 = loader.read_uint64()
        self.flags = loader.read_byte()  # Texture Info
        self.dimensions = loader.read_byte()
        self.tile_mode = loader.read_uint16()
        self.swizzle_size = loader.read_uint16()
        mipmap_cnt = loader.read_uint16()
        self.multisample_cnt = loader.read_uint16()
        reserved = loader.read_uint16()
        self.fmt_dtype = BRTI.TextureDataType(loader.read_byte())
        self.format_ = TextureFormat.get(loader.read_byte())()
        loader.seek(2)
        access_flags = loader.read_uint32()
        self.width = loader.read_int32()
        self.height = loader.read_int32()
        self.depth = loader.read_int32()
        array_cnt = loader.read_uint32()
        texture_layout = loader.read_uint32()
        texture_layout2 = loader.read_uint32()
        loader.seek(20)
        data_len = loader.read_uint32()
        self.alignment = loader.read_uint32()
        self.channel_types = loader.read_bytes(4)
        tex_type = loader.read_int32()
        self.name = loader.load_string()
        parent_offset = loader.read_offset()
        ptrs_offset = loader.read_offset()

        self.fmt_id = self.format_.id
        self.bpp = bpps[self.fmt_id]

        if (self.fmt_id) in blk_dims:
            self.blk_width, self.blk_height = blk_dims[self.fmt_id]
        else:
            self.blk_width, self.blk_height = 1, 1
        self.blk_height_log2 = texture_layout & 7

        with loader.temporary_seek(ptrs_offset):
            for i in range(mipmap_cnt):
                entry = loader.read_uint32()  # - base
                loader.seek(4)
                self.mip_offsets.append(entry)

        self.__read_data(loader, ptrs_offset, data_len)
        self.pixels = self.format_.decompress(self)

    class ChannelType(IntEnum):
        ZERO = 0
        ONE = 1
        RED = 2
        GREEN = 3
        BLUE = 4
        ALPHA = 5

    class TextureType(IntEnum):
        IMAGE1D = 0
        IMAGE2D = 1
        IMAGE3D = 2
        CUBE = 3
        CUBEFAR = 8

    class TextureDataType(IntEnum):
        UNORM = 1
        SNORM = 2
        UINT = 3
        SINT = 4
        SINGLE = 5
        SRGB = 6
        UHALF = 10

    def __read_data(self, loader: core.ResFileLoader, ptrs_offset, data_len):
        """Read the raw image data."""
        loader.seek(ptrs_offset, io.SEEK_SET)
        loader.seek(loader.read_uint64(), io.SEEK_SET)
        self.data = loader.read_bytes(data_len)

        lines_per_blk_height = (1 << self.blk_height_log2) * 8
        blk_height_shift = 0
        mip_offset = self.mip_offsets[0]

        size = div_round_up(self.width, self.blk_width) * \
            div_round_up(self.height, self.blk_height) * self.bpp

        if (pow2_round_up(div_round_up(self.height, self.blk_height)) < lines_per_blk_height):
            blk_height_shift += 1

        result = deswizzle(
            self.width, self.height, self.blk_width, self.blk_height, self.bpp, self.tile_mode,
            max(0, self.blk_height_log2 - blk_height_shift), self.data,
        )

        self.mip_data = result[:size]
