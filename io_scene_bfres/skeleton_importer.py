import math

import bpy
import mathutils


class SkeletonImporter:
    def __init__(self, parent):
        self.operator = parent.operator

    def _convert_fskl(self, fmdl, fskl, collection):
        name = fmdl.name
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)

        amt = bpy.data.armatures.new(name=name + ".Armature")
        amt.relation_line_position = "HEAD"
        arm_obj = bpy.data.objects.new(name=name, object_data=amt)

        collection.objects.link(arm_obj)
        bpy.context.view_layer.objects.active = arm_obj

        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        bone_objs = {}
        for i, bone in enumerate(fskl.bones.values()):
            bone_obj = amt.edit_bones.new(name=bone.name)
            bone_objs[i] = bone_obj
            bone_obj.use_relative_parent = True
            bone_obj.use_local_location = True

            bone_obj.length = 0.1
            if bone.parent_idx >= 0:
                bone_obj.parent = bone_objs[bone.parent_idx]
                bone_obj.matrix = bone_obj.parent.matrix @ self.__bone_matrix(bone)
            else:
                matrix = self.__bone_matrix(bone)

                bone_obj.matrix = mathutils.Matrix.Rotation(math.radians(90), 4, (1, 0, 0)) @ matrix
            bone.matrix = bone_obj.matrix
        bpy.ops.object.mode_set(mode="OBJECT")

        if fskl.flags_rotation.name == "EULER_XYZ":
            for pb in arm_obj.pose.bones:
                pb.rotation_mode = "XYZ"

        return arm_obj

    @staticmethod
    def __bone_matrix(obj):
        L = mathutils.Vector(obj.position[0:3])
        if obj.bone_flags_rotation.name == "EULER_XYZ":
            R = mathutils.Euler(obj.rotation[0:3])
        else:
            R = mathutils.Quaternion(obj.rotation)
        S = mathutils.Vector(obj.scale[0:3])
        M = mathutils.Matrix.LocRotScale(L, R, S)

        return M
