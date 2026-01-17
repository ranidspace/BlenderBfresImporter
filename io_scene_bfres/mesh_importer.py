import logging
import struct

import bmesh
import bpy
import mathutils
import numpy as np

from .attribute import AttributeFormat
from .bfrespy.gx2 import GX2PrimitiveType
from .exceptions import MalformedFileError

log = logging.getLogger(__name__)

PRIMITIVE_TYPES = {
    GX2PrimitiveType.POINTS: (1, 1, "point_list"),
    GX2PrimitiveType.LINES: (2, 2, "line_list"),
    GX2PrimitiveType.LINE_STRIP: (2, 1, "line_strip"),
    GX2PrimitiveType.TRIANGLES: (3, 3, "triangle_list"),
}


def __get_vtx_attributes(fvtx, first_vtx: int) -> dict:
    attributes = {}
    num_vtx = fvtx.vtx_count - first_vtx

    for attribute in fvtx.attributes.values():
        buffer = fvtx.buffers[attribute.buffer_idx]
        fmt = AttributeFormat(attribute.format_.value)

        data = [None] * num_vtx
        for i in range(num_vtx):
            try:
                offset = (first_vtx + i) * buffer.stride
                data[i] = struct.unpack_from(fmt.read, buffer.data[0], offset)
            except struct.error as e:
                message = f"Vertex {i} reading out of bounds for attribute '{attribute.name}'"
                raise MalformedFileError(message) from e

        data = np.array(data)
        if fmt.func:
            data = fmt.func(data)

        # Check if normalized
        elif fmt.AttribType.INTEGER not in fmt.flags and fmt.AttribType.SCALED not in fmt.flags:  # SNORM
            if fmt.AttribType.SIGNED in fmt.flags:
                data = np.where(data == fmt.min, -1, np.divide(data, fmt.max))
            # UNORM
            else:
                data = np.divide(data, fmt.max)

        attributes[attribute.name] = data
    return attributes


def import_mesh(fmdl, fshp, lod_idx, custom_normals) -> bpy.types.Object:
    mesh = fshp.meshes[min(lod_idx, len(fshp.meshes) - 1)]

    lod_vtx_attribs = __get_vtx_attributes(fshp.vtx_buffer, mesh.first_vtx)

    bm = bmesh.new()
    create_mesh_data(bm, fmdl, fshp, mesh, lod_vtx_attribs)

    blender_mesh = bpy.data.meshes.new(name=fshp.name)
    bm.to_mesh(blender_mesh)
    bm.free()

    mesh_ob = bpy.data.objects.new(name=blender_mesh.name, object_data=blender_mesh)

    add_uv_maps(mesh_ob, lod_vtx_attribs)
    add_vtx_weights(mesh_ob, fmdl, fshp, lod_vtx_attribs)

    if custom_normals:
        add_split_normals(mesh_ob, lod_vtx_attribs, fshp, fmdl)
    if "_c0" in lod_vtx_attribs:
        add_vtx_colors(mesh_ob, lod_vtx_attribs["_c0"])
    return mesh_ob


def _get_face_indices(lod_mesh):
    idx_buff = lod_mesh.index_buffer.data[0]
    match lod_mesh.index_format.name:
        case "UINT16_LITTLE_ENDIAN":
            indices = np.frombuffer(idx_buff, dtype="<H")
        case "UINT32_LITTLE_ENDIAN":
            indices = np.frombuffer(idx_buff, dtype="<I")
        case _:
            raise ValueError("Invalid index buffer value %s", lod_mesh.index_format.name)
    return indices


def create_mesh_data(bm, fmdl, fshp, mesh, vtx_attribs):
    """Go through the vertices (starting at the given offset) and add them to the bmesh."""
    indices = _get_face_indices(mesh)
    log.debug("LOD has %d vtxs, %d idxs", len(vtx_attribs), len(indices))

    for i in range(len(vtx_attribs["_p0"])):
        try:
            vtx_pos = mathutils.Vector(vtx_attribs["_p0"][i][0:3])
        except IndexError:
            log.exception("Index out of bounds")
            raise

        match fshp.vtx_skin_count:
            case 0:
                midx = fshp.bone_idx
                matrix = fmdl.skeleton.bones[midx].matrix
                vtx_pos = matrix @ vtx_pos
            case 1:
                midx = vtx_attribs["_i0"][i][0]
                matrix = fmdl.skeleton.bones[fmdl.skeleton.mtx_to_bone_list[midx]].matrix
                vtx_pos = matrix @ vtx_pos
            case _:
                vtx_pos = mathutils.Vector((vtx_pos.x, -vtx_pos.z, vtx_pos.y))
        bm.verts.new(vtx_pos)

    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

    # Create the faces.
    fmt = PRIMITIVE_TYPES[mesh.primitive_type]
    try:
        return _create_faces(indices, bm, fmt[0], fmt[1])
    except (struct.error, IndexError) as e:
        raise MalformedFileError("LOD submesh faces are out of bounds") from e


def _create_faces(idxs, mesh, step, num_vtxs):
    for i in range(0, len(idxs), step):
        try:
            vs = [mesh.verts[j] for j in idxs[i : i + num_vtxs]]
            # log.debug("face %d: %s", i, vs)
            face = mesh.faces.new(vs)
            face.smooth = True
        except IndexError:
            log.exception("LOD submesh face %d is out of bounds (max %d)", i, len(idxs))
            raise
        except ValueError:
            pass


def add_split_normals(mesh_ob: bpy.types.Object, lod_vtxs, fshp, fmdl):
    normals = []

    for v in mesh_ob.data.vertices:
        normal = mathutils.Vector(lod_vtxs["_n0"][v.index][0:3])
        match fshp.vtx_skin_count:
            case 0:
                matrix_id = fshp.bone_idx
                matrix = fmdl.skeleton.bones[matrix_id].matrix
                normal = _rotate_normal(matrix, normal)

            case 1:
                matrix_id = lod_vtxs["_i0"][v.index][0]
                matrix = fmdl.skeleton.bones[fmdl.skeleton.mtx_to_bone_list[matrix_id]].matrix
                normal = _rotate_normal(matrix, normal)
            case _:
                normal = mathutils.Vector((normal.x, -normal.z, normal.y))
        normals.append(normal)

    mesh_ob.data.normals_split_custom_set_from_vertices(normals)


def _rotate_normal(matrix, normal) -> mathutils.Vector:
    rotation = matrix.decompose()[1]
    return rotation @ normal


def add_vtx_colors(mesh_ob: bpy.types.Object, colors):
    mdata = mesh_ob.data
    vertex_colors = mdata.color_attributes.new(name="_c0", type="FLOAT_COLOR", domain="POINT")

    for v in mdata.vertices:
        col = colors[v.index]
        vertex_colors.data[v.index].color_srgb = col


def add_uv_maps(mesh_ob, lod_vtxs):
    for attr in lod_vtxs:
        if len(attr) != 3 or attr[:2] != "_u":
            continue
        mdata = mesh_ob.data
        uv_layer = mdata.uv_layers.new(name=attr)
        for poly in mdata.polygons:
            for loop_idx in poly.loop_indices:
                loop = mdata.loops[loop_idx]
                uvloop = uv_layer.data[loop_idx]
                x, y = lod_vtxs[attr][loop.vertex_index][:2]
                y = 1 - y
                uvloop.uv.x, uvloop.uv.y = x, y


def add_vtx_weights(mesh_ob: bpy.types.Object, fmdl, fshp, lod_vtxs):
    """Make vertex group for mesh object from attributes."""
    groups = {}

    # no i0 or w0, mesh is parented to the bone_idx
    if fshp.vtx_skin_count == 0:
        idx = fshp.bone_idx
        grp = mesh_ob.vertex_groups.new(name=fmdl.skeleton.bones[idx].name)
        grp.add(range(len(lod_vtxs["_p0"])), 1, "REPLACE")
        return

    # Add vertex groups for all bones
    for bone in fmdl.skeleton.bones.values():
        grp = mesh_ob.vertex_groups.new(name=bone.name)
        groups[bone.smooth_mtx_idx] = grp
        groups[bone.rigid_mtx_idx] = grp

    if fshp.vtx_skin_count == 1:
        # i0 specifies the bone rigid matrix group.
        for vertex_id in range(len(lod_vtxs["_i0"])):
            idx = lod_vtxs["_i0"][vertex_id][0]
            groups[idx].add([vertex_id], 1, "REPLACE")
        return
    for vertex_id in range(len(lod_vtxs["_i0"])):
        # Smooth skinning, bone index and weight
        weight = lod_vtxs["_w0"][vertex_id][: fshp.vtx_skin_count]
        idx = lod_vtxs["_i0"][vertex_id]
        for i in range(fshp.vtx_skin_count):
            if weight[i] > 0 and idx[i] in groups:
                groups[idx[i]].add([vertex_id], weight[i] / 255.0, "REPLACE")
