from ..bfrespy import core
from .brti import BRTI
import logging
import io
log = logging.getLogger(__name__)


class NX(core.ResData):
    """An NX texture in a BNTX."""

    def __init__(self):
        self.textures = []

    def load(self, loader: core.ResFileLoader):
        target_platform = loader.read_raw_string(4, 'ascii')
        tex_count = loader.read_int32()
        tex_table_array = loader.read_offset()
        tex_data_ptr = loader.read_uint64()
        tex_dict_offs = loader.read_uint64()
        mem_pool_ptr = loader.read_uint64()
        user_mem_pool_ptr = loader.read_uint64()
        base_mem_pool_offs = loader.read_uint32()
        reserved = loader.read_uint32()

        loader.seek(tex_table_array, io.SEEK_SET)
        for i in range(tex_count):
            self.textures.append(loader.load(BRTI))
