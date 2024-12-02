from blf import load
import bpy
import bmesh
import numpy as np
import mathutils
import struct
import logging
from .bfrespy.gx2 import GX2PrimitiveType
from .material_importer import MaterialImporter
from .exceptions import UnsupportedFormatError, MalformedFileError

log = logging.getLogger(__name__)


class MeshImporter:
    def __init__(self, parent):
        self.parent = parent

    def _convert_lod(self, fvtx, fmdl, fshp, lod):
        self.fvtx = fvtx
        self.fmdl = fmdl
        self.fshp = fshp
        self.lod = lod
        self.lod_name = self.fshp.name

        self.mesh_ob = self.__create_mesh()

        if (self.parent.operator.custom_normals):
            self.__add_split_normals()
        if (self.lod_vtxs[0].get('_c0')):
            self.__add_vtx_colors()
        self.__add_uv_map()
        self.__add_vtx_weights()
        self.__add_armature()

        return self.mesh_ob

    def __create_mesh(self):
        idx_buff = self.lod.index_buffer.data[0]
        match self.lod.index_format.name:
            case "UINT16_LITTLE_ENDIAN":
                self.indices = np.frombuffer(idx_buff, dtype='<H')
            case "UINT32_LITTLE_ENDIAN":
                self.indices = np.frombuffer(idx_buff, dtype='<I')
            case _:
                raise ValueError("Replace this error")

        last_vertex = max(self.indices) + 1
        self.lod_vtxs = self.fvtx[self.lod.first_vtx:self.lod.first_vtx + last_vertex]
        log.debug("LOD has %d vtxs, %d idxs", len(self.lod_vtxs), len(self.indices))

        # Create a bmesh to represent the FSHP polygon.
        bm = bmesh.new()
        self.__add_verts_to_mesh(bm)
        self.__create_faces(bm)

        fshp_mesh = bpy.data.meshes.new(name=self.lod_name)
        bm.to_mesh(fshp_mesh)
        bm.free()
        mesh_ob = bpy.data.objects.new(name=fshp_mesh.name, object_data=fshp_mesh)
        mdata = mesh_ob.data

        mat = self.fmdl.materials[self.fshp.material_idx]
        mdata.materials.append(bpy.data.materials[mat.name])

        return mesh_ob

    def __add_verts_to_mesh(self, bm):
        """Go through the vertices (starting at the given offset) and add them to the bmesh."""
        for i, vertex in enumerate(self.lod_vtxs):
            try:
                if (len(vertex['_p0']) == 4):
                    x, y, z, w = vertex['_p0']
                else:
                    x, y, z = vertex['_p0']
                    w = 1
                if (w != 1):
                    # Blender doesn't support the W coord, but it's never used anyway.
                    log.warning("FRES: FSHP vertex #%d W coord is %f, should be 1", i, w)
            except IndexError:
                # logger
                raise
            match self.fshp.vtx_skin_count:
                case 0:
                    midx = self.fshp.bone_idx
                    M = self.fmdl.skeleton.bones[midx].matrix
                    P = mathutils.Vector((x, y, z))
                    P = M @ P
                    x, y, z = P
                    vert = bm.verts.new((x, y, z))
                case 1:
                    midx = vertex['_i0'][0]
                    M = self.fmdl.skeleton.bones[self.fmdl.skeleton.mtx_to_bone_list[midx]].matrix
                    P = mathutils.Vector((x, y, z))
                    P = M @ P
                    x, y, z = P
                    vert = bm.verts.new((x, y, z))
                case _:
                    vert = bm.verts.new((x, -z, y))

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

    def __create_faces(self, bm):
        """Create the faces."""
        fmt = self.lod.primitive_type
        fmt = self.__prim_types[fmt]
        method = getattr(self, '_create_faces_' + fmt[2], None)
        if (method is None):
            log.error("Unsupported primitive format: %s", fmt)
            raise UnsupportedFormatError("Unsupported prim format: " + fmt[2])
        try:
            return method(self.indices, bm)
        except (struct.error, IndexError):
            raise MalformedFileError("LOD submesh faces are out of bounds")

    __prim_types = {
        GX2PrimitiveType.POINTS: (1, 1, 'point_list'),
        GX2PrimitiveType.LINES: (2, 2, 'line_list'),
        GX2PrimitiveType.LINE_STRIP: (2, 1, 'line_strip'),
        GX2PrimitiveType.TRIANGLES: (3, 3, 'triangle_list'),
    }

    def __create_faces_basic(self, idxs, mesh, step, nVtxs):
        for i in range(0, len(idxs), step):
            try:
                vs = list(mesh.verts[j] for j in idxs[i:i + nVtxs])
                # log.debug("face %d: %s", i, vs)
                face = mesh.faces.new(vs)
                face.smooth = True
            except IndexError:
                log.error("LOD submesh face %d is out of bounds (max %d)", i, len(idxs))
                raise

    def _create_faces_point_list(self, idxs, mesh):
        return self.__create_faces_basic(idxs, mesh, 1, 1)

    def _create_faces_line_list(self, idxs, mesh):
        return self.__create_faces_basic(idxs, mesh, 2, 2)

    def _create_faces_line_strip(self, idxs, mesh):
        return self.__create_faces_basic(idxs, mesh, 1, 2)

    def _create_faces_triangle_list(self, idxs, mesh):
        return self.__create_faces_basic(idxs, mesh, 3, 3)

    def __add_split_normals(self):
        normals = []
        mdata = self.mesh_ob.data

        for v in mdata.vertices:
            x, y, z = self.lod_vtxs[v.index]['_n0'][0:3]
            match self.fshp.vtx_skin_count:
                case 0:
                    midx = self.fshp.bone_idx
                    M = self.fmdl.skeleton.bones[midx].matrix
                    M = M.decompose()[1]
                    P = mathutils.Vector((x, y, z))
                    P = M @ P

                case 1:
                    midx = self.lod_vtxs[v.index]['_i0'][0]
                    M = self.fmdl.skeleton.bones[self.fmdl.skeleton.mtx_to_bone_list[midx]].matrix
                    M = M.decompose()[1]
                    P = mathutils.Vector((x, y, z))
                    P = M @ P
                case _:
                    P = mathutils.Vector((x, -z, y))
            normals.append(P)

        mdata.normals_split_custom_set_from_vertices(normals)

    def __add_vtx_colors(self):
        mdata = self.mesh_ob.data
        vertex_colors = mdata.color_attributes.new(name='_c0', type='FLOAT_COLOR', domain='POINT')

        for v in mdata.vertices:
            col = self.lod_vtxs[v.index]['_c0']
            vertex_colors.data[v.index].color_srgb = col

    def __add_uv_map(self):
        idx = 0
        while True:
            attr = '_u%d' % idx
            if (self.fvtx[0].get(attr, None) is None):
                break
            mdata = self.mesh_ob.data
            uv_layer = mdata.uv_layers.new(name=attr)
            for i, poly in enumerate(mdata.polygons):
                for j, loop_idx in enumerate(poly.loop_indices):
                    loop = mdata.loops[loop_idx]
                    uvloop = uv_layer.data[loop_idx]
                    x, y = self.lod_vtxs[loop.vertex_index][attr][:2]
                    y = 1 - y
                    uvloop.uv.x, uvloop.uv.y = x, y
            idx += 1

    def __add_vtx_weights(self):
        """Add vertex weights (`_w0` attribute) to mesh."""
        try:
            self.__make_vtx_group()
        except KeyError:
            # log.info("mesh '%s' has no weights", self.lod_name)
            pass

    def __make_vtx_group(self):
        """Make vertex group for mesh object from attributes."""
        # XXX move to SkeletonImporter?
        groups = {}

        # i0 = self.attrBuffers.get('_i0')
        # w0 = self.attrBuffers.get('_w0')

        # create a vertex group for each bone
        # each bone affects the vertex group with the same
        # name as that bone, and these weights define how much.
        if (self.fshp.vtx_skin_count == 0):
            # no i0 or w0, mesh is parented to the bone it's on
            idx = self.fshp.bone_idx
            grp = self.mesh_ob.vertex_groups.new(name=self.fmdl.skeleton.bones[idx].name)

            for i in range(len(self.lod_vtxs)):
                grp.add([i], 1, 'REPLACE')
        else:
            for bone in self.fmdl.skeleton.bones.values():
                grp = self.mesh_ob.vertex_groups.new(name=bone.name)
                groups[bone.smooth_mtx_idx] = grp
                groups[bone.rigid_mtx_idx] = grp

            if (self.fshp.vtx_skin_count == 1):
                # i0 specifies the bone rigid matrix group.
                for i in range(0, len(self.lod_vtxs)):
                    idx = self.lod_vtxs[i]['_i0'][0]
                    groups[idx].add([i], 1, 'REPLACE')
            else:
                # i0 specifies the bone smooth matrix group.
                # Look for a bone with the same group.
                for i in range(0, len(self.lod_vtxs)):
                    # how much this bone affects this vertex
                    wgt = self.lod_vtxs[i]['_w0'][:self.fshp.vtx_skin_count]
                    idx = self.lod_vtxs[i]['_i0']  # which bone index group
                    for j, w in enumerate(wgt):
                        if (w > 0):
                            try:
                                groups[idx[j]].add([i], w / 255.0, 'REPLACE')
                            except (KeyError, IndexError):
                                # log.warning("Bone group %d doesn't exist (referenced by weight of vtx %d, value %d)",
                                #             idx[j], i, w)
                                pass

    def __add_armature(self):
        """Add armature to mesh."""
        mod = self.mesh_ob.modifiers.new(name=self.lod_name, type='ARMATURE')
        mod.object = self.parent.fskl_ob
        mod.use_bone_envelopes = False
        mod.use_vertex_groups = True
        return mod
