from dataclasses import dataclass
from enum import IntFlag, IntEnum

from ..core import ResData, ResFileLoader
from ..common import ResDict, Buffer
from ..gx2 import GX2PrimitiveType, GX2IndexFormat
from ..switch.memory_pool import MemoryPool, BufferSize, BufferInfo
from . import VertexBuffer


class Shape(ResData):
    """Represents an FSHP section in a Model subfile"""
    _SIGNATURE = "FSHP"

    def __init__(self):
        self.name = ""
        self.flags = ShapeFlags.HAS_VERTEX_BUFFER
        self.material_idx = 0
        self.bone_idx = 0
        self.vtx_buff_idx = 0
        self.radius_array = []
        self.bounding_radius_list: list[tuple[float, float, float, float]] = []
        self.vtx_skin_count = 0
        self.target_attrib_count = 0
        self.meshes: list[Mesh] = []
        self.skin_bone_idxs = tuple()
        self.key_shapes: ResDict[KeyShape] = ResDict()
        self.submesh_boundings: list[Bounding] = []
        self.submesh_bounding_nodes: list[BoundingNode] = []
        self.submesh_bounding_idxs = []
        self.vtx_buffer = VertexBuffer()

    @property
    def has_vtx_buffer(self):
        return ShapeFlags.HAS_VERTEX_BUFFER in self.flags

    @has_vtx_buffer.setter
    def has_vtx_buffer(self, value):
        if (value):
            self.flags |= ShapeFlags.HAS_VERTEX_BUFFER
        else:
            self.flags &= ShapeFlags.HAS_VERTEX_BUFFER

    @property
    def submesh_boundary_consistent(self):
        return ShapeFlags.SUBMESH_BOUNDARY_CONSISTENT in self.flags

    @has_vtx_buffer.setter
    def has_vtx_buffer(self, value):
        if (value):
            self.flags |= ShapeFlags.SUBMESH_BOUNDARY_CONSISTENT
        else:
            self.flags &= ShapeFlags.SUBMESH_BOUNDARY_CONSISTENT

    def load(self, loader: ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        if (loader.is_switch):
            from ..switch.model import ShapeParser
            ShapeParser.read(loader, self)


class Mesh(ResData):
    """Represents the surface net of a Shape section, storing information on
    which index Buffer to use for referencing vertices of theshape, mostly used
    for different levels of detail (LoD) models.
    """

    def __init__(self):
        self.primitive_type = GX2PrimitiveType.TRIANGLES
        """The GX2PrimitiveType which determines how indices are used to 
        form polygons.
        """

        self.index_format = GX2IndexFormat.UINT16
        """The GX2IndexFormat determining the data type of the indices in the
        IndexBuffer.
        """

        self.submeshes = []
        """List of SubMesh instances which split up a mesh into parts which can
        be hidden if they are not visible to optimize rendering performance.
        """

        self.index_buffer = Buffer()
        """The Buffer storing the index data"""

        self.mempool = MemoryPool()

        self.first_vtx: int
        """The offset to the first vertex element of a VertexBuffer to 
        reference by indices.
        """

    @property
    def index_count(self):
        """Gets the number of indices stored in the IndexBuffer"""
        element_count = 0
        format_size = self.format_size
        for i in range(len(self.index_buffer.data)):
            buffering_size = len(self.index_buffer.data[i])
            if (buffering_size % format_size != 0):
                raise ValueError(
                    f"Cannot form complete indices from {self.index_buffer}.")
            element_count += buffering_size / format_size
        return element_count

    @property
    def data(self):
        return self.index_buffer.data[0]

    @property
    def format_size(self):
        match (self.index_format):
            case (GX2IndexFormat.UINT16
                  | GX2IndexFormat.UINT16_LITTLE_ENDIAN):
                return 2
            case (GX2IndexFormat.UINT32
                  | GX2IndexFormat.UINT32_LITTLE_ENDIAN):
                return 4
            case _:
                raise ValueError(f"Invalid GX2IndexFormat \
                                 {self.index_format.name}.")

    @property
    def format_byte_order(self):
        match (self.index_format):
            case (GX2IndexFormat.UINT16_LITTLE_ENDIAN
                    | GX2IndexFormat.UINT32_LITTLE_ENDIAN):
                return '<'
            case (GX2IndexFormat.UINT16
                    | GX2IndexFormat.UINT32):
                return '>'
            case _:
                raise ValueError(
                    f"Invalid GX2IndexFormat{self.index_format.name}."
                )

    def load(self, loader: ResFileLoader):
        if (loader.is_switch):
            submesh_array_offs = loader.read_offset()
            self.mempool = loader.load(MemoryPool)
            buffer = loader.read_offset()
            buffer_size = loader.load(BufferSize)
            face_buff_offs = loader.read_uint32()
            self.primitive_type = self.primitive_type_list[
                self.SwitchPrimitiveType(loader.read_uint32())
            ]
            self.index_format = self.index_list[
                self.SwitchIndexFormat(loader.read_uint32())
            ]
            index_count = loader.read_uint32()
            self.first_vtx = loader.read_uint32()
            num_submesh = loader.read_uint16()
            padding = loader.read_uint16()
            self.submeshes = loader.load_list(
                SubMesh, num_submesh, offset=submesh_array_offs
            )
            data_offs = BufferInfo.buff_offs + face_buff_offs

            self.index_buffer = Buffer()
            self.index_buffer.flags = buffer_size.flags
            self.index_buffer.data = [b'']
            self.index_buffer.data[0] = loader.load_custom(
                bytes, lambda: loader.read_bytes(buffer_size.size), data_offs
            )

    class SwitchIndexFormat(IntEnum):
        UNSIGNED_BYTE = 0
        UINT16 = 1
        UINT32 = 2

    class SwitchPrimitiveType(IntEnum):
        POINTS = 0X00
        LINES = 0X01
        LINE_STRIP = 0X02
        TRIANGLES = 0X03
        TRIANGLE_STRIP = 0X04
        LINES_ADJACENCY = 0X05
        LINE_STRIP_ADJACENCY = 0X06
        TRIANGLES_ADJACENCY = 0X07
        TRIANGLE_STRIP_ADJACENCY = 0X08
        PATCHES = 0X09

    index_list = {
        SwitchIndexFormat.UINT16: GX2IndexFormat.UINT16_LITTLE_ENDIAN,
        SwitchIndexFormat.UINT32: GX2IndexFormat.UINT32_LITTLE_ENDIAN,
        SwitchIndexFormat.UNSIGNED_BYTE: GX2IndexFormat.UINT16_LITTLE_ENDIAN,
    }

    primitive_type_list = {
        SwitchPrimitiveType.TRIANGLES: GX2PrimitiveType.TRIANGLES,
        SwitchPrimitiveType.TRIANGLES_ADJACENCY: GX2PrimitiveType.TRIANGLES_ADJACENCY,
        SwitchPrimitiveType.TRIANGLE_STRIP: GX2PrimitiveType.TRIANGLE_STRIP_ADJACENCY,
        SwitchPrimitiveType.TRIANGLE_STRIP_ADJACENCY: GX2PrimitiveType.TRIANGLE_STRIP_ADJACENCY,
        SwitchPrimitiveType.LINES: GX2PrimitiveType.LINES,
        SwitchPrimitiveType.LINES_ADJACENCY: GX2PrimitiveType.LINES_ADJACENCY,
        SwitchPrimitiveType.LINE_STRIP: GX2PrimitiveType.LINE_STRIP,
        SwitchPrimitiveType.LINE_STRIP_ADJACENCY: GX2PrimitiveType.LINE_STRIP_ADJACENCY,
        SwitchPrimitiveType.POINTS: GX2PrimitiveType.POINTS,
    }


class SubMesh(ResData):
    def __init__(self):
        self.offset: int
        self.count: int

    def __repr__(self) -> str:
        return "Submesh[{" + str(self.offset) + "},{" + str(self.count) + "}]"

    def load(self, loader: ResFileLoader):
        self.offset = loader.read_uint32()
        self.count = loader.read_uint32()


class KeyShape(ResData):
    def __init__(self):
        self.target_attrib_idx: bytes
        self.target_attrib_idx_offs: bytes

    def load(self, loader: ResFileLoader):
        self.target_attrib_idx = loader.read_bytes(20)
        self.target_attrib_idx_offs = loader.read_bytes(4)


class BoundingNode(ResData):
    """Represents a node in a SubMesh bounding tree to determine when to show 
    which sub mesh of a Mesh
    """

    def __init__(self):
        self.left_child_idx: int
        self.next_sibling: int
        self.right_child_idx: int
        self.unk: int
        self.submesh_idx: int
        self.submesh_cnt: int

    def load(self, loader: ResFileLoader):
        self.left_child_idx = loader.read_uint16()
        self.next_sibling = loader.read_uint16()
        self.right_child_idx = loader.read_uint16()
        self.unk = loader.read_uint16()
        self.submesh_idx = loader.read_uint16()
        self.submesh_cnt = loader.read_uint16()


@dataclass
class Bounding:
    """Represents a spatial bounding box."""
    center: tuple[float, float, float]
    extent: tuple[float, float, float]

    def __repr__(self) -> str:
        return "Bounding[{" + str(self.center) + "},{" + str(self.extent) + "}]"


class ShapeFlags(IntFlag):
    """Represents flags determining which data is available for 
    Shape instances
    """
    HAS_VERTEX_BUFFER = 1 << 1
    SUBMESH_BOUNDARY_CONSISTENT = 1 << 2
