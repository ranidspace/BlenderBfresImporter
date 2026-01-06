from ..switchcore import ResFileSwitchLoader
from ...models import Model, Shape, Skeleton, Material, VertexBuffer
from ...common import UserData, Buffer


class ModelParser:
    @staticmethod
    def read(loader: ResFileSwitchLoader, model: Model):
        if (loader.res_file.version_major2 >= 9):
            model.flags = loader.read_uint32()
        else:
            loader.load_header_block()

        model.name = loader.load_string()
        model.path = loader.load_string()
        model.skeleton = loader.load(Skeleton)
        vtx_array_offs = loader.read_offset()
        model.shapes = loader.load_dict_values(Shape)
        if (loader.res_file.version_major2 == 9):
            material_vals_offs = loader.read_offset()
            off = loader.read_offset()  # padding?
            material_dict_offs = loader.read_offset()
            if (material_dict_offs == 0):
                material_dict_offs = off

            model.materials = loader.load_dict_values(
                Material, material_dict_offs, material_vals_offs)
        else:
            material_vals_offs = loader.read_offset()
            material_dict_offs = loader.read_offset()
            model.materials = loader.load_dict_values(
                Material, material_dict_offs, material_vals_offs)
            if (loader.res_file.version_major2 >= 10):
                loader.read_offset()  # Shader assign offset

        model.userdata = loader.load_dict_values(UserData)
        user_pointer = loader.read_offset()
        num_vtx_buff = loader.read_uint16()
        num_shape = loader.read_uint16()
        num_material = loader.read_uint16()

        num_user_data = 0
        if (loader.res_file.version_major2 >= 9):
            loader.read_uint16()  # shader assign count
            num_user_data = loader.read_uint16()
            loader.read_uint16()  # padding?
            padding = loader.read_uint32()
        else:
            num_user_data = loader.read_uint16()
            total_vtx_count = loader.read_uint32()
            padding = loader.read_uint32()

        model.vtx_buffers = loader.load_list(
            VertexBuffer, num_vtx_buff, int(vtx_array_offs)
        )
