import bpy
import mathutils as mu

from .bfrespy.animhelper import CurveAnimHelper
from .bfrespy.common import AnimCurveType
from .bfrespy.skeletal_anim import BoneAnimFlagsBase


class BoneAnimationImporter:
    def __init__(self, parent):
        self.parent = parent

    def _import_animations(self, bfres):
        """Import Bone animations from FSKA"""
        # import all bones
        self.scene_bones: dict[str, tuple[mu.Vector, mu.Quaternion | mu.Euler, mu.Vector]] = {}
        for fmdl in bfres.models.values():
            for bone in fmdl.skeleton.bones.values():
                L = mu.Vector(bone.position[0:3])
                if bone.bone_flags_rotation.name == "EULER_XYZ":
                    R = mu.Euler(bone.rotation[0:3])
                else:
                    R = mu.Quaternion(bone.rotation)
                S = mu.Vector(bone.scale[0:3])

                self.scene_bones[bone.name] = (L, R, S)

        for fska in bfres.skeletal_anims.values():
            action = bpy.data.actions.new(name=fska.name)
            action.use_frame_range = True
            action.frame_start = 0
            action.frame_end = fska.frame_cnt
            action.use_cyclic = fska.loop
            if self.parent.operator.add_fake_user:
                action.use_fake_user = True

            for bone_anim in fska.bone_anims:
                if (init_transform := self.scene_bones.get(bone_anim.name)) is None:
                    init_transform = (mu.Vector((0, 0, 0)), mu.Quaternion((1, 0, 0, 0)), mu.Vector((1, 1, 1)))

                action_group = bone_anim.name
                self.__import_base_data(fska, action, init_transform, bone_anim, action_group)

                continue

                # TODO import full animations
                #
                # I've given this a shot but and I know it's doable but I'd have to rewrite a lot.
                # Animations are stored relative to the parent bone, but blender stores it relative to starting
                # position. While it works for importing the base data, it's impossible to do rotational transforms
                # without knowing all the details of the animation, which would need knowing what value all the
                # rotational curves are at on every frame. I believe they're hermite curves, but formatted oddly. The
                # Curve Anim helper works though.

                # This code should not run; It's the progress I have in importing the rotational curves so far.
                i = 0
                rot_curves = [None] * 3
                for i, curve in enumerate(bone_anim.curves):
                    typ, idx = bone_anim.curve_flag[i].name.split("_")
                    i += 1
                    idx = _coord_to_idx[idx]
                    rot_curves[idx] = curve
                    CurveAnimHelper.from_curve(curve, bone_anim.curve_flag[i + 1].name, use_degrees=False)

                for i, frame in enumerate(fska.frame_cnt):
                    x = self.__get_curve_frame_val(rot_curves[0], frame) if rot_curves[0] else init_transform[0]

    @staticmethod
    def __import_base_data(fska, action, init_transform, bone_anim, action_group):
        """Import base data from bone_anim to the first frame of a blender action."""
        if BoneAnimFlagsBase.TRANSLATE in bone_anim.flags_base:
            translate = mu.Vector(bone_anim.base_data.translate) - init_transform[0]
            for i, val in enumerate(translate):
                fcurve = action.fcurves.new(
                    data_path='pose.bones["' + action_group + '"].location', index=i, action_group=action_group
                )
                fcurve.keyframe_points.insert(frame=0, value=val)

        if BoneAnimFlagsBase.ROTATE in bone_anim.flags_base:
            if fska.flags_rotate.name == "EULER_XYZ":
                inverted = init_transform[1].to_matrix().inverted()
                rot = mu.Euler(bone_anim.base_data.rotate[:3]).to_matrix()
                rot = (inverted @ rot).to_euler()
                for i, val in enumerate(rot):
                    fcurve = action.fcurves.new(
                        data_path='pose.bones["' + action_group + '"].rotation_euler',
                        index=i,
                        action_group=action_group,
                    )
                    fcurve.keyframe_points.insert(frame=0, value=val)
            else:
                rot = mu.Quaternion(bone_anim.base_data.rotate)
                rot = init_transform[1].inverted() @ rot
                for i, val in enumerate(rot):
                    fcurve = action.fcurves.new(
                        data_path='pose.bones["' + action_group + '"].rotation_quaternion',
                        index=i,
                        action_group=action_group,
                    )
                    fcurve.keyframe_points.insert(frame=0, value=val)

        if BoneAnimFlagsBase.SCALE in bone_anim.flags_base:
            # Component-wise division
            scale = mu.Vector(
                (
                    bone_anim.base_data.scale[0] / init_transform[2][0],
                    bone_anim.base_data.scale[1] / init_transform[2][1],
                    bone_anim.base_data.scale[2] / init_transform[2][2],
                )
            )
            for i, val in enumerate(scale):
                fcurve = action.fcurves.new(
                    data_path='pose.bones["' + action_group + '"].scale', index=i, action_group=action_group
                )
                fcurve.keyframe_points.insert(frame=0, value=val)

    @staticmethod
    def __get_curve_frame_val(curve, num):
        """Return the value at the specific frame of a curve"""
        frame = max(frame for frame, key in curve.keyframes if frame <= num)
        keyframe = curve.keyframes[frame]
        if frame == num:
            return keyframe.value

        t = num - frame
        if curve.key_type == AnimCurveType.CUBIC:
            ...


_flagcurve_to_fcurve = {
    "SCALE": "scale",
    "ROTATE": "rotation_euler",
    "TRANSLATE": "location",
}

_coord_to_idx = {
    "X": 0,
    "Y": 1,
    "Z": 2,
    "W": 3,
}
