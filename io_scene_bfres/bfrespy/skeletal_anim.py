from __future__ import annotations
from enum import IntFlag
from . import core
from . import common
from . import models


class SkeletonAnim(core.ResData):
    """Represents an FSKA subfile in a ResFile, storing armature animations of
    Bone instances in a Skeleton.
    """
    _SIGNATURE = "FSKA"
    _FLAGS_MASK_SCALE = 0b00000000_00000000_00000011_00000000
    _FLAGS_MASK_ROTATE = 0B00000000_00000000_01110000_00000000
    _FLAGS_MASK_ANIM_SETTINGS = 0b00000000_00000000_00000000_00001111

    class SkeletalAnimFlags(IntFlag):
        # 32 bit
        BAKED_CURVE = 1 << 0
        """The stored curve data has been baked."""

        LOOPING = 1 << 2
        """The animation repeats from the start after 
        the last frame has been played.
        """

    class SkeletalAnimFlagsScale(IntFlag):
        # 32 bit
        NONE = 0
        """No Scaling."""

        STANDARD = 1 << 8
        """Default Scaling."""

        MAYA = 2 << 8
        """Autodesk Maya scaling."""

        SOFTIMAGE = 3 << 8
        """Autodesk Softimage scaling."""

    class SkeletalAnimFlagsRotate(IntFlag):
        QUATERNION = 0
        """Quaternion, 4 components."""

        EULER_XYZ = 1 << 12
        """Euler XYZ, 3 components."""

    def __init__(self) -> None:
        self._flags = 0
        self.name = ''
        self.path = ''
        self.flags_anim_settings = 0
        self.flags_scale = self.SkeletalAnimFlagsScale.MAYA
        self.flags_rotate = self.SkeletalAnimFlagsRotate.EULER_XYZ
        self.frame_cnt = 0
        self.baked_size = 0
        self.bone_anims: list[BoneAnim] = []
        self.bind_skeleton = models.Skeleton()
        self.bind_idxs: tuple[int, ...] = tuple()
        self.userdata: common.ResDict[common.UserData] = common.ResDict()

    def __repr__(self):
        return "SkeletonAnim" + "{" + self.name + "}"

    @property
    def flags_anim_settings(self) -> SkeletalAnimFlags:
        """The SkeletalAnimFlags mode used
        to control looping and baked settings.
        """
        return self.SkeletalAnimFlags(
            self._flags & self._FLAGS_MASK_ANIM_SETTINGS
        )

    @flags_anim_settings.setter
    def flags_anim_settings(self, value: int):
        self._flags &= ~self._FLAGS_MASK_ANIM_SETTINGS | value

    @property
    def loop(self) -> bool:
        return self.SkeletalAnimFlags.LOOPING in self.flags_anim_settings

    @loop.setter
    def loop(self, value: bool):
        if (value):
            self.flags_anim_settings |= self.SkeletalAnimFlags.LOOPING
        else:
            self.flags_anim_settings &= ~self.SkeletalAnimFlags.LOOPING

    @property
    def baked(self) -> bool:
        return self.SkeletalAnimFlags.BAKED_CURVE in self.flags_anim_settings

    @baked.setter
    def baked(self, value: bool):
        if (value):
            self.flags_anim_settings |= self.SkeletalAnimFlags.BAKED_CURVE
        else:
            self.flags_anim_settings &= ~self.SkeletalAnimFlags.BAKED_CURVE

    @property
    def flags_scale(self) -> SkeletalAnimFlagsScale:
        """The SkeletalAnimFlags mode used
        to control looping and baked settings.
        """
        return self.SkeletalAnimFlagsScale(
            self._flags & self._FLAGS_MASK_SCALE
        )

    @flags_scale.setter
    def flags_scale(self, value: SkeletalAnimFlagsScale):
        self._flags &= ~self._FLAGS_MASK_SCALE | value

    @property
    def flags_rotate(self) -> SkeletalAnimFlagsRotate:
        """The SkeletalAnimFlags mode used
        to control looping and baked settings.
        """
        return self.SkeletalAnimFlagsRotate(
            self._flags & self._FLAGS_MASK_ROTATE
        )

    @flags_rotate.setter
    def flags_rotate(self, value: SkeletalAnimFlagsRotate):
        self._flags &= ~self._FLAGS_MASK_ROTATE | value

    def load(self, loader: core.ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        if (loader.is_switch):
            if (loader.res_file.version_major2 >= 9):
                self._flags = loader.read_uint32()
            else:
                loader.load_header_block()

            self.name = loader.load_string()
            self.path = loader.load_string()
            self.bind_skeleton = loader.load(models.Skeleton)
            bind_idx_array = loader.read_offset()
            bone_anim_array_offset = loader.read_offset()
            self.userdata = loader.load_dict_values(common.UserData)
            if (loader.res_file.version_major2 < 9):
                self._flags = loader.read_uint32()

            self.frame_cnt = loader.read_int32()
            num_curve = loader.read_int32()
            self.baked_size = loader.read_uint32()
            num_bone_anim = loader.read_uint16()
            num_userdata = loader.read_uint16()

            if (loader.res_file.version_major2 < 9):
                loader.read_uint32()  # Padding

            self.bone_anims = loader.load_list(
                BoneAnim, num_bone_anim, bone_anim_array_offset
            )
            self.bind_idxs = loader.load_custom(
                tuple, lambda: loader.read_int16s(num_bone_anim),
                bind_idx_array
            )
        else:
            num_bone_anim = 0
            if (loader.res_file.version >= 0x02040000):
                self.name = loader.load_string()
                self.path = loader.load_string()
                self._flags = loader.read_uint32()

                if (loader.res_file.version >= 0x03040000):
                    self.frame_cnt = loader.read_int32()
                    num_bone_anim = loader.read_uint16()
                    num_userdata = loader.read_uint16()
                    num_curve = loader.read_int32()
                    self.baked_size = loader.read_uint32()
                else:
                    self.frame_cnt = loader.read_uint16()
                    num_bone_anim = loader.read_uint16()
                    num_userdata = loader.read_uint16()
                    num_curve = loader.read_uint16()
                    self.baked_size = loader.read_uint32()
                    loader.seek(4)  # padding

                self.bone_anims = loader.load_list(BoneAnim, num_bone_anim)
                self.bind_skeleton = loader.load(models.Skeleton)
                self.bind_idxs = loader.load_custom(
                    tuple, lambda: loader.read_int16s(num_bone_anim)
                )
                self.userdata = loader.load_dict(common.UserData)
            else:
                self._flags = loader.read_uint32()
                self.frame_cnt = loader.read_uint16()
                num_bone_anim = loader.read_uint16()
                num_userdata = loader.read_uint16()
                num_curve = loader.read_uint16()
                self.name = loader.load_string()
                self.path = loader.load_string()
                self.bone_anims = loader.load_list(BoneAnim, num_bone_anim)
                self.bind_skeleton = loader.load(models.Skeleton)
                self.bind_idxs = loader.load_custom(
                    tuple, lambda: loader.read_int16s(num_bone_anim)
                )


class BoneAnim(core.ResData):
    """Represents the animation of a single Bone in a SkeletalAnim subfile."""
    _FLAGS_MASK_BASE = 0b00000000_00000000_00000000_00111000
    _FLAGS_MASK_CURVE = 0B00000000_00000000_11111111_11000000
    _FLAGS_MASK_TRANSFORM = 0b00001111_10000000_00000000_00000000

    def __init__(self):
        self.name = ""
        self._flags = 0
        self.flags_base = 0
        self.begin_rotate = 0
        self.begin_translate = 0
        self.begin_base_translate = 0

        self.curves: list[common.AnimCurve] = []
        self.base_data: BoneAnimData
        self.begin_curve = 0

    def __repr__(self):
        return "BoneAnim" + "{" + self.name + "}"

    @property
    def flags_base(self) -> BoneAnimFlagsBase:
        """The SkeletalAnimFlags mode used
        to control looping and baked settings.
        """
        return BoneAnimFlagsBase(
            self._flags & self._FLAGS_MASK_BASE
        )

    @flags_base.setter
    def flags_base(self, value: BoneAnimFlagsBase):
        self._flags &= ~self._FLAGS_MASK_BASE | value

    @property
    def flags_curve(self) -> BoneAnimsFlagCurve:
        """The SkeletalAnimFlags mode used
        to control looping and baked settings.
        """
        return BoneAnimsFlagCurve(
            self._flags & self._FLAGS_MASK_CURVE
        )

    @flags_curve.setter
    def flags_curve(self, value: BoneAnimsFlagCurve):
        self._flags &= ~self._FLAGS_MASK_CURVE | value

    @property
    def flags_transform(self) -> BoneAnimFlagsTransform:
        """The SkeletalAnimFlags mode used
        to control looping and baked settings.
        """
        return BoneAnimFlagsTransform(
            self._flags & self._FLAGS_MASK_TRANSFORM
        )

    @flags_transform.setter
    def flags_transform(self, value: BoneAnimFlagsTransform):
        self._flags &= ~self._FLAGS_MASK_TRANSFORM | value

    def load(self, loader: core.ResFileLoader):
        if (loader.is_switch):
            self.name = loader.load_string()
            curve_offs = loader.read_offset()
            base_data_offs = loader.read_offset()
            if (loader.res_file.version_major2 >= 9):
                unk1 = loader.read_int64()
                unk2 = loader.read_int64()
            self._flags = loader.read_uint32()
            self.begin_rotate = loader.read_byte()
            self.begin_translate = loader.read_byte()
            num_curve = loader.read_byte()
            self.begin_base_translate = loader.read_byte()
            self.begin_curve = loader.read_int32()
            padding = loader.read_int32()

            self.base_data = loader.load_custom(
                BoneAnimData, lambda: BoneAnimData(loader, self.flags_base),
                base_data_offs
            )
            self.curves = loader.load_list(
                common.AnimCurve, num_curve, curve_offs
            )
        else:
            self._flags = loader.read_uint32()
            self.name = loader.load_string()
            self.begin_rotate = loader.read_byte()
            self.begin_translate = loader.read_byte()
            num_curve = loader.read_byte()
            self.begin_base_translate = loader.read_byte()
            self.begin_curve = loader.read_byte()
            self.curves = loader.load_list(common.AnimCurve, num_curve)
            self.base_data = loader.load_custom(
                BoneAnimData, lambda: BoneAnimData(loader, self.flags_base)
            )


class BoneAnimFlagsBase(IntFlag):
    """Represents if initial values exist for the corresponding transformation
    in the base animation data.
    """
    SCALE = 1 << 3
    """Initial scaling values exist."""
    ROTATE = 1 << 4
    """Initial rotation values exist."""
    TRANSLATE = 1 << 5
    """Initial translation values exist."""


class BoneAnimsFlagCurve(IntFlag):
    SCALE_X = 1 << 6
    """Curve animating the X component of a bone's scale."""
    SCALE_Y = 1 << 7
    """Curve animating the Y component of a bone's scale."""
    SCALE_Z = 1 << 8
    """Curve animating the Z component of a bone's scale."""
    ROTATE_X = 1 << 9
    """Curve animating the X component of a bone's rotation."""
    ROTATE_Y = 1 << 10
    """Curve animating the Y component of a bone's rotation."""
    ROTATE_Z = 1 << 11
    """Curve animating the Z component of a bone's rotation."""
    ROTATE_W = 1 << 12
    """Curve animating the W component of a bone's rotation."""
    TRANSLATE_X = 1 << 13
    """Curve animating the X component of a bone's translation."""
    TRANSLATE_Y = 1 << 14
    """Curve animating the Y component of a bone's translation."""
    TRANSLATE_Z = 1 << 15
    """Curve animating the Z component of a bone's translation."""


class BoneAnimFlagsTransform(IntFlag):
    SEGMENT_SCALE_COMPENSATE = 1 << 23
    SCALE_UNIFORM = 1 << 24
    SCALE_VOLUME_ONE = 1 << 25
    ROTATE_ZERO = 1 << 26
    TRANSLATE_ZERO = 1 << 27
    SCALE_ONE = SCALE_VOLUME_ONE | SCALE_UNIFORM
    ROTATE_TRANSLATE_ZERO = ROTATE_ZERO | TRANSLATE_ZERO
    IDENTITY = SCALE_ONE | ROTATE_ZERO | TRANSLATE_ZERO


class BoneAnimData:
    """Represents the animatable data of a Bone instance."""

    def __init__(self, loader: core.ResFileLoader, flags):
        self._flags = 0  # Never in files.
        self.scale = (loader.read_vector3f()
                      if BoneAnimFlagsBase.SCALE in flags
                      else (1, 1, 1))
        self.rotate = (loader.read_vector4f()
                       if BoneAnimFlagsBase.ROTATE in flags
                       else (1, 0, 0, 0))
        padding = 0
        self.translate = (loader.read_vector3f()
                          if BoneAnimFlagsBase.TRANSLATE in flags
                          else (0, 0, 0))
