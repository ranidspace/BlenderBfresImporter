from enum import IntFlag
from ..core import ResData, ResFileLoader
from ..common import ResDict, UserData


class Bone(ResData):
    """Represents a single bone in a Skeleton section, storing its initial 
    transform and transformation effects.
    """

    _FLAGS_MASK = 0B00000000_00000000_00000000_00000001
    _FLAGS_MASK_ROTATE = 0B00000000_00000000_01110000_00000000
    _FLAGS_MASK_BILLBOARD = 0B00000000_00000111_00000000_00000000
    _FLAGS_MASK_TRANSFORM = 0B00001111_00000000_00000000_00000000
    _FLAGS_MASK_TRANSFORM_CUMULATIVE = 0B11110000_00000000_00000000_00000000

    def __init__(self):
        _flags = 0
        self.name = ""
        self.userdata = ResDict()
        self.parent_idx = -1
        self.smooth_mtx_idx = -1
        self.rigid_mtx_idx = -1
        self.billboard_idx = -1

        self.scale = (1, 1, 1)
        self.rotation = (0, 0, 0, 0)
        self.position = (0, 0, 0)

        self.flags = BoneFlags.VISIBLE
        self.flags_rotation = BoneFlagsRotation.EULER_XYZ
        self.flags_billboard = BoneFlagsBillboard.NONE
        self.flags_transform = BoneFlagsTransform.NONE
        self.flags_transform_cumulative = BoneFlagsTransformCumulative.NONE

    def __repr__(self):
        return "Bone{" + str(self.name) + "}"

    # Properties

    @property
    def visible(self):
        return BoneFlags.VISIBLE in self.flags

    @visible.setter
    def visible(self, value):
        if (value):
            self.flags |= BoneFlags.VISIBLE
        else:
            self.flags &= BoneFlags.VISIBLE

    @property
    def bone_flags(self):
        return BoneFlags(self._flags & self._FLAGS_MASK)

    @bone_flags.setter
    def bone_flags(self, value):
        self._flags &= ~self._FLAGS_MASK | int(value)

    @property
    def bone_flags_rotation(self):
        return BoneFlagsRotation(self._flags & self._FLAGS_MASK_ROTATE)

    @bone_flags_rotation.setter
    def bone_flags_rotation(self, value):
        self._flags &= ~self._FLAGS_MASK_ROTATE | int(value)

    @property
    def bone_flags_billboard(self):
        return BoneFlagsBillboard(self._flags & self._FLAGS_MASK_BILLBOARD)

    @bone_flags_billboard.setter
    def bone_flags_billboard(self, value):
        self._flags &= ~self._FLAGS_MASK_BILLBOARD | int(value)

    @property
    def bone_flags_transform(self):
        return BoneFlagsTransform(self._flags & self._FLAGS_MASK_TRANSFORM)

    @bone_flags_transform.setter
    def bone_flags_transform(self, value):
        self._flags &= ~self._FLAGS_MASK_TRANSFORM | int(value)

    @property
    def bone_flags_transform_cumulative(self):
        return BoneFlagsTransformCumulative(
            self._flags & self._FLAGS_MASK_TRANSFORM_CUMULATIVE)

    @bone_flags_transform_cumulative.setter
    def bone_flags_transform_cumulative(self, value):
        self._flags &= ~self._FLAGS_MASK_TRANSFORM_CUMULATIVE | int(value)

    @property
    def userdata_list(self):
        return self.userdata.values()

    # Methods

    def load(self, loader: ResFileLoader):
        if (loader.is_switch):
            self.name = loader.load_string()
            self.userdata = loader.load_dict_values(UserData)
            if (loader.res_file.version_major2 > 9):
                loader.seek(8)

            if (loader.res_file.version_major2 == 8
                    or loader.res_file.version_major2 == 9):
                loader.seek(16)

            idx = loader.read_int16()
            self.parent_idx = loader.read_int16()
            self.smooth_mtx_idx = loader.read_int16()
            self.rigid_mtx_idx = loader.read_int16()
            self.billboard_idx = loader.read_int16()
            num_user_data = loader.read_uint16()
            self._flags = loader.read_uint32()
            self.scale = loader.read_vector3f()
            self.rotation = loader.read_vector4f()
            self.position = loader.read_vector3f()
        else:
            self.name = loader.load_string()
            idx = loader.read_uint16()
            self.parent_idx = loader.read_int16()
            self.smooth_mtx_idx = loader.read_int16()
            self.rigid_mtx_idx = loader.read_int16()
            self.billboard_idx = loader.read_int16()
            num_user_data = loader.read_uint16()
            _flags = loader.read_uint32()
            self.scale = loader.read_vector3f()
            self.rotation = loader.read_vector4f()
            self.position = loader.read_vector3f()
            self.userdata = loader.load_dict(UserData)

            if (loader.res_file.version < 0x03040000):
                self.inverse_mtx = loader.read_matrix_3x4()


class BoneFlags(IntFlag):
    """Represents flags controlling bone behavior"""

    VISIBLE = 1
    """Set when the bone is visible."""


class BoneFlagsRotation(IntFlag):
    """Represents the rotation method used to store bone rotations."""

    QUATERNION = 0
    """A quaternion represents the rotation."""
    EULER_XYZ = 1 << 12
    """A Vector3F represents the Euler rotation in XYZ order."""


class BoneFlagsBillboard(IntFlag):
    """Represents the possible transformations for bones to handle them as billboards."""

    NONE = 0
    """No transformation is applied."""

    CHILD = 1 << 16
    """Transforms of the child are applied."""

    WORLD_VIEW_VECTOR = 2 << 16
    """Transforms the Z axis parallel to the camera."""

    WORLD_VIEW_POINT = 3 << 16
    """Transforms the Z axis parallel to the direction of the camera."""

    SCREEN_VIEW_VECTOR = 4 << 16
    """Transforms the Y axis parallel to the camera up vector,
    and the Z parallel to the camera up-vector.
    """

    SCREEN_VIEW_POINT = 5 << 16
    """Transforms the Y axis parallel to the camera up vector, and the
    Z axis parallel to the direction of the camera.
    """

    Y_AXIS_VIEW_VECTOR = 6 << 16
    """Transforms the Z axis parallel to the camera by
    rotating only the Y axis.
    """

    Y_AXIS_VIEW_POINT = 7 << 16
    """Transforms the Z axis parallel to the direction of the camera
    by rotating only the Y axis.
    """


class BoneFlagsTransform(IntFlag):
    NONE = 0
    SCALE_UNIFORM = 1 << 24
    SCALE_VOLUME_ONE = 1 << 25
    ROTATE_ZERO = 1 << 26
    TRANSLATE_ZERO = 1 << 27
    SCALE_ONE = SCALE_UNIFORM | SCALE_VOLUME_ONE
    ROTATE_TRANSLATE_ZERO = ROTATE_ZERO | TRANSLATE_ZERO
    IDENTITY = SCALE_ONE | ROTATE_ZERO | TRANSLATE_ZERO


class BoneFlagsTransformCumulative(IntFlag):
    NONE = 0
    SCALE_UNIFORM = 1 << 28
    SCALE_VOLUME_ONE = 1 << 29
    ROTATE_ZERO = 1 << 30
    TRANSLATE_ZERO = 1 << 31
    SCALE_ONE = SCALE_VOLUME_ONE | SCALE_UNIFORM
    ROTATE_TRANSLATE_ZERO = ROTATE_ZERO | TRANSLATE_ZERO
    IDENTITY = SCALE_ONE | ROTATE_ZERO | TRANSLATE_ZERO


class Skeleton(ResData):
    """Represents an FSKL section in a Model subfile, storing armature data."""
    _SIGNATURE = "FSKL"
    _FLAGS_SCALING_MASK = 0b00000000_00000000_00000011_00000000
    _FLAGS_ROTATION_MASK = 0b00000000_00000000_01110000_00000000

    def __init__(self):
        self._flags = 0
        self.num_smooth_mtxs: int
        self.num_rigid_mtxs: int
        self.user_idxs: tuple

        self.mtx_to_bone_list = []
        self.inverse_model_mtxs = []
        self.bones = ResDict()
        self.flags_rotation = SkeletonFlagRotation.EULER_XYZ
        self.flags_scaling = SkeletonFlagScaling.MAYA

    def __bool__(self):
        return len(self.bones) != 0

    # Properties

    @property
    def flags_scaling(self):
        return SkeletonFlagScaling(self._flags & self._FLAGS_SCALING_MASK)

    @flags_scaling.setter
    def flags_scaling(self, value):
        self._flags &= ~self._FLAGS_SCALING_MASK | int(value)

    @property
    def flags_rotation(self):
        return SkeletonFlagRotation(self._flags & self._FLAGS_ROTATION_MASK)

    @flags_rotation.setter
    def flags_rotation(self, value):
        self._flags &= ~self._FLAGS_ROTATION_MASK | int(value)

    @property
    def bonelist(self):
        self.bones.values()

    def get_smooth_idxs(self):
        idxs = []
        for bone in self.bones.values():
            if (bone.smooth_mtx_idx != 1):
                idxs.append(bone.smooth_mtx_idx)
        return idxs

    def get_rigid_idxs(self):
        idxs = []
        for bone in self.bones.values():
            if (bone.rigid_mtx_idx != 1):
                idxs.append(bone.rigid_mtx_idx)
        return idxs

    # Methods

    def load(self, loader: ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        if (loader.is_switch):
            if (loader.res_file.version_major2 >= 9):
                self._flags = loader.read_uint32()
            else:
                offset = loader.read_uint32()
                size = loader.read_uint64()

            bone_dict_offs = loader.read_offset()
            bone_array_offs = loader.read_offset()
            self.bones = loader.load_dict_values(
                Bone, bone_dict_offs, bone_array_offs
            )
            mtx_to_bone_list_offs = loader.read_offset()
            inverse_model_mtx_offs = loader.read_offset()

            if (loader.res_file.version_major2 == 8):
                loader.seek(16)
            if (loader.res_file.version_major2 >= 9):
                loader.seek(8)

            user_pointer = loader.read_int64()
            if (loader.res_file.version_major2 < 9):
                self._flags = loader.read_uint32()
            num_bone = loader.read_uint16()
            self.num_smooth_mtxs = loader.read_uint16()
            self.num_rigid_mtxs = loader.read_uint16()
            loader.seek(6)

            self.user_idxs = loader.load_custom(
                tuple, lambda: loader.read_uint16s(num_bone), user_pointer
            )

            self.mtx_to_bone_list = (
                loader.load_custom(
                    list, lambda: loader.read_uint16s(
                        self.num_smooth_mtxs + self.num_rigid_mtxs),
                    mtx_to_bone_list_offs)
            )
            self.inverse_model_mtxs = (
                loader.load_custom(
                    list, lambda: loader.read_matrix_3x4s(
                        self.num_smooth_mtxs),
                    inverse_model_mtx_offs
                )
            )


class SkeletonFlagScaling(IntFlag):
    NONE = 0
    STANDARD = 1 << 8
    MAYA = 2 << 8
    SOFTIMAGE = 3 << 8


class SkeletonFlagRotation(IntFlag):
    """Represents the rotation method used to store bone rotations."""

    QUATERNION = 0
    """A quaternion represents the rotation."""

    EULER_XYZ = 1 << 12
    """A Vector3F represents the Euler rotation in XYZ order."""
