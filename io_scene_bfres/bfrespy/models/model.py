from ..core import ResData, ResFileLoader
from ..common import ResDict, UserData

from .skeleton import Skeleton
from .vertex_buffer_attrib import VertexBuffer
from .shape import Shape
from .material import Material


class Model(ResData):
    """Represents an FMDL subfile in a ResFile, storing model vertex data, 
    skeletons and used materials.
    """
    _SIGNATURE = "FMDL"

    def __init__(self):
        "Initializes a new instance of the Model class."
        self.name = ""
        self.path = ""
        self.skeleton = Skeleton()
        self.vtx_buffers: list[VertexBuffer] = []
        self.shapes = ResDict()
        self.materials = ResDict()
        self.userdata = ResDict()

        self.flags: int

    @property
    def total_vtx_count(self):
        """Gets the total number of vertices to process
        when drawing this model.
        """
        count = 0
        for vtx_buffer in self.vtx_buffers:
            count += vtx_buffer.vtx_count
        return count

    def load(self, loader: ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        if (loader.is_switch):
            from ..switch.model import ModelParser
            ModelParser.read(loader, self)
        else:
            self.name = loader.load_string()
            self.path = loader.load_string()
            self.skeleton = loader.load(Skeleton)
            ofs_vtx_buffer_list = loader.read_offset()
            self.shapes = loader.load_dict(Shape)
            self.materials = loader.load_dict(Material)
            self.userdata = loader.load_dict(UserData)
            num_vtx_buffer = loader.read_uint16()
            num_shape = loader.read_uint16()
            num_material = loader.read_uint16()
            num_userdata = loader.read_uint16()
            total_vtx_count = loader.read_uint32()

            if (loader.res_file.version >= 0x03030000):
                user_pointer = loader.read_uint32()
            self.vtx_buffers = loader.load_list(
                VertexBuffer, num_vtx_buffer, ofs_vtx_buffer_list,
            )
