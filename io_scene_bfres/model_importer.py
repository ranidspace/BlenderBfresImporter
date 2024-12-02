import bpy
import bpy_extras
import bmesh
import math
import mathutils
import struct
import numpy as np
from .skeleton_importer import SkeletonImporter
from .mesh_importer import MeshImporter
from .attribute import AttributeFormat
from .material_importer import MaterialImporter
from .exceptions import MalformedFileError

import logging
log = logging.getLogger(__name__)


class ModelImporter:
    def __init__(self, parent):
        self.operator = parent.operator
        self.context = parent.context

    def _convert_fmdl(self, fmdl, collection):
        skel_imp = SkeletonImporter(self)
        self.fskl_ob = skel_imp._convert_fskl(fmdl, fmdl.skeleton, collection)

        # Import all Materials for this model
        mat_imp = MaterialImporter(self, fmdl)
        for i, fmat in enumerate(fmdl.materials.values()):
            log.info("Importing material %3d / %3d...",
                     i + 1, len(fmdl.materials))
            mat_imp.import_material(fmat)

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
        vertices = [{} for _ in range(fvtx.vtx_count)]
        for attribute in fvtx.attributes.values():
            vtx_member = attribute.name
            buffer = fvtx.buffers[attribute.buffer_idx]
            fmt = AttributeFormat(attribute.format_.value)
            for i, offset in enumerate(range(0, len(buffer.data[0]), buffer.stride)):

                try:
                    data = struct.unpack_from(fmt.read, buffer.data[0], offset)
                except struct.error:
                    log.error("Submesh %d reading out of bounds for attribute '%s' (offs=0x%X len=0x%X fmt=%s)",
                              i, vtx_member, offset, len(buffer.data), fmt
                              )
                    raise MalformedFileError(
                        "Submesh {idx} reading out of bounds for attribute '{name}'".format(idx=i, name=vtx_member)
                    )

                if (fmt.func):
                    data = fmt.func(data)

                # Check if normalized
                elif (fmt.AttribType.INTEGER not in fmt.flags
                      and fmt.AttribType.SCALED not in fmt.flags):
                    d = []
                    # SNORM
                    if (fmt.AttribType.SIGNED in fmt.flags):
                        for num in data:
                            # python should make this a float regardless
                            if (num == fmt.min):
                                d.append(-1)
                            else:
                                d.append(num / fmt.max)
                    # UNORM
                    else:
                        for num in data:
                            # python should make this a float regardless
                            d.append(num / fmt.max)
                    data = tuple(d)

                d = data
                if (type(d) not in (list, tuple)):
                    d = (d)
                    # validate
                for v in d:
                    if (type(v) is float):
                        if (math.isinf(v) or math.isnan(v)):
                            log.warning("value in attribute %s is infinity or NaN", vtx_member)
                            print("value in attribute is infinity or nan")

                vertices[i][vtx_member] = data
        return vertices
