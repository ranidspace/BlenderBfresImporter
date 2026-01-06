import io
from ..switchcore import ResFileSwitchLoader
from ...models import Shape, ShapeFlags, Mesh, VertexBuffer, KeyShape


class ShapeParser:
    @staticmethod
    def read(loader: ResFileSwitchLoader, shape: Shape):
        if (loader.res_file.version_major2 >= 9):
            shape.flags = ShapeFlags(loader.read_int32())
        else:
            loader.load_header_block()

        shape.name = loader.load_string()
        shape.vtx_buffer = loader.load(VertexBuffer)
        mesh_array_offs = loader.read_offset()
        skin_bone_idx_list_offs = loader.read_offset()
        shape.key_shapes = loader.load_dict_values(KeyShape)
        bounding_box_array_offs = loader.read_offset()
        radius_offs = 0
        if (loader.res_file.version_major2 > 2
                or loader.res_file.version_major > 0):
            radius_offs = loader.read_offset()
            user_pointer = loader.read_int64()
        else:
            user_pointer = loader.read_int64()
            shape.radius_array.append(loader.read_single())
        if (loader.res_file.version_major2 < 9):
            shape.flags = ShapeFlags(loader.read_int32())
        idx = loader.read_uint16()
        shape.material_idx = loader.read_uint16()
        shape.bone_idx = loader.read_uint16()
        shape.vtx_buff_idx = loader.read_uint16()
        num_skin_bone_idx = loader.read_uint16()
        shape.vtx_skin_count = loader.read_byte()
        num_mesh = loader.read_byte()
        num_keys = loader.read_byte()
        num_target_attr = loader.read_byte()
        if (loader.res_file.version_major2 <= 2
                and loader.res_file.version_major == 0):
            loader.seek(2)  # padding
        elif (loader.res_file.version_major2 >= 9):
            loader.seek(2)  # padding
        else:
            loader.seek(6)  # padding

        shape.radius_array = []
        if (radius_offs != 0 and num_mesh > 0):
            with (loader.temporary_seek(radius_offs, io.SEEK_SET)):
                if (loader.res_file.version_major2 >= 10):
                    # A offset + radius size. Can be per mesh or per bone if there is skinning used.
                    num_boundings = (num_mesh
                                     if num_skin_bone_idx == 0
                                     else num_skin_bone_idx)
                    for i in range(num_boundings):
                        shape.bounding_radius_list.append(
                            loader.read_vector4f())
                    # Get largest radius for bounding radius list
                    max_ = max([x[3] for x in shape.bounding_radius_list])
                    shape.radius_array.append(max_)
                else:
                    shape.radius_array = list(loader.read_singles(num_mesh))

        shape.meshes = ([]
                        if num_mesh == 0
                        else loader.load_list(Mesh, num_mesh, mesh_array_offs)
                        )
        shape.skin_bone_idxs = (
            ()
            if num_skin_bone_idx == 0
            else loader.load_custom(
                tuple, lambda: loader.read_uint16s(num_skin_bone_idx),
                skin_bone_idx_list_offs
            )
        )

        bounding_box_cnt = sum(
            [len(mesh.submeshes) + 1 for mesh in shape.meshes]
        )
        shape.submesh_boundings = (
            []
            if bounding_box_cnt == 0
            else loader.load_custom(
                list, lambda: loader.read_boundings(bounding_box_cnt),
                bounding_box_array_offs))

        shape.submesh_bounding_nodes = []
