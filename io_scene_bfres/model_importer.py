import logging
import struct

import numpy as np

from .attribute import AttributeFormat
from .exceptions import MalformedFileError
from .material_importer import MaterialImporter
from .mesh_importer import MeshImporter
from .skeleton_importer import SkeletonImporter

log = logging.getLogger(__name__)


class ModelImporter:
    def __init__(self, parent):
        self.operator = parent.operator
        self.texture_map = parent.texture_map
        self.material_map: dict

    def _convert_fmdl(self, fmdl, collection):
        skel_imp = SkeletonImporter(self)
        self.fskl_ob = skel_imp._convert_fskl(fmdl, fmdl.skeleton, collection)

        # Import all Materials for this model
        mat_imp = MaterialImporter(self, fmdl)
        self.material_map = {}
        for i, fmat in enumerate(fmdl.materials.values()):
            log.info("Importing material %3d / %3d...", i + 1, len(fmdl.materials))
            mat_imp.import_material(fmat, self.texture_map, self.material_map)

        # Go through the polygons in this model and create mesh objects representing them.
        for i, fshp in enumerate(fmdl.shapes.values()):
            log.info("Importing shape %3d / %3d '%s'...", i + 1, len(fmdl.shapes), fshp.name)
            fshp_ob = self._convert_fshp(fmdl, fshp, collection)
            fshp_ob.parent = self.fskl_ob
            # Parent to the empty FMDL object and link it to the scene.

    def _convert_fshp(self, fmdl, fshp, collection):
        # Get the vertices and indices of the closest LoD model.
        fvtx = self.__get_vertices(fmdl.vtx_buffers[fshp.vtx_buff_idx])
        lod_model = fshp.meshes[min(self.operator.lod_index, len(fshp.meshes) - 1)]

        mesh_imp = MeshImporter(self)
        mesh_obj = mesh_imp._convert_lod(fvtx, fmdl, fshp, lod_model)
        collection.objects.link(mesh_obj)

        return mesh_obj

    @staticmethod
    def __get_vertices(fvtx) -> list:
        vertices = {}
        for attribute in fvtx.attributes.values():
            vtx_atrribute = attribute.name
            buffer = fvtx.buffers[attribute.buffer_idx]
            fmt = AttributeFormat(attribute.format_.value)

            data = [None] * fvtx.vtx_count
            for i in range(fvtx.vtx_count):
                try:
                    offset = i * buffer.stride
                    data[i] = struct.unpack_from(fmt.read, buffer.data[0], offset)
                except struct.error as e:
                    log.exception(
                        "Submesh %d reading out of bounds for attribute '%s' (offs=0x%X len=0x%X fmt=%s)",
                        i,
                        vtx_atrribute,
                        offset,
                        len(buffer.data),
                        fmt,
                    )
                    raise MalformedFileError(
                        "Submesh {idx} reading out of bounds for attribute '{name}'".format(idx=i, name=vtx_atrribute)
                    ) from e

            data = np.array(data)

            if fmt.func:
                data = fmt.func(data)

            # Check if normalized
            elif fmt.AttribType.INTEGER not in fmt.flags and fmt.AttribType.SCALED not in fmt.flags:
                # SNORM
                if fmt.AttribType.SIGNED in fmt.flags:
                    np.where(data == fmt.min, -1, np.divide(data, fmt.max))
                # UNORM
                else:
                    data = np.divide(data, fmt.max)

            vertices[vtx_atrribute] = data
        return [dict(zip(vertices, t, strict=True)) for t in zip(*vertices.values(), strict=True)]
