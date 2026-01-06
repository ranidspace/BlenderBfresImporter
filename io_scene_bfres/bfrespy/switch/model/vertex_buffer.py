import io
from ...core import ResData
from ..memory_pool import MemoryPool, BufferInfo
from ..switchcore import ResFileSwitchLoader
from ...models import VertexBuffer, VertexAttrib
from ...common import UserData, Buffer


class VertexBufferStride(ResData):
    def __init__(self):
        self.stride: int

    def __repr__(self):
        return "VertexBufferStride{" + str(self.stride) + "}"

    def load(self, loader: ResFileSwitchLoader):
        self.stride = loader.read_uint32()
        loader.seek(12)


class VertexBufferSize(ResData):

    def __init__(self):
        self.size: int
        self.gpu_access_flags: int

    def __repr__(self):
        return "VertexBufferSize{" + str(self.size) + "}"

    def load(self, loader: ResFileSwitchLoader):
        self.size = loader.read_uint32()
        self.gpu_access_flags = loader.read_uint32()
        loader.seek(8)


class VertexBufferParser:
    @staticmethod
    def load(loader: ResFileSwitchLoader, vtx_buffer: VertexBuffer):
        if (loader.res_file.version_major2 >= 9):
            vtx_buffer.flags = loader.read_uint32()
        else:
            loader.load_header_block()

        vtx_buffer.attributes = loader.load_dict_values(VertexAttrib)
        vtx_buffer.mempool = loader.load(MemoryPool)
        unk = loader.read_offset()
        if (loader.res_file.version_major2 > 2
                or loader.res_file.version_major > 0):
            loader.read_offset()  # unk2
        vtx_buff_size_offs = loader.read_offset()
        vtx_stride_size_offs = loader.read_offset()
        padding = loader.read_int64()
        buff_offs = loader.read_int32()
        num_vtx_attrib = loader.read_byte()
        num_buffer = loader.read_byte()
        idx = loader.read_uint16()
        vtx_buffer.vtx_count = loader.read_uint32()
        vtx_buffer.vtx_skin_count = loader.read_uint16()
        vtx_buffer.gpu_buff_align = loader.read_uint16()

        # Buffers use the index buffer offset from memory info section.
        # This goes to a section in the memory pool which stores all the
        # buffer data, including faces.
        # To obtain a list of all the buffer data, it would be by the
        # index buffer offset + buff_offs.

        stride_array = loader.load_list(
            VertexBufferStride, num_buffer, vtx_stride_size_offs
        )
        vtx_buff_size_array = loader.load_list(
            VertexBufferSize, num_buffer, vtx_buff_size_offs
        )

        vtx_buffer.buffers = []
        with (loader.temporary_seek(BufferInfo.buff_offs + buff_offs, io.SEEK_SET)):
            for buff in range(num_buffer):
                buffer = Buffer()
                buffer.data = [b'']
                buffer.stride = stride_array[buff].stride

                loader.align(8)
                buffer.data[0] = loader.read_bytes(
                    vtx_buff_size_array[buff].size
                )
                vtx_buffer.buffers.append(buffer)
