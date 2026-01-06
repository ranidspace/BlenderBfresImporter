import math
from enum import IntEnum, auto
from typing import Any
from ..binary_io import BinaryReader

from .. import core, gx2
from ..common import (ResDict, ResString, TextureRef, UserData,
                      Srt2D, Srt3D, TexSrt, TexSrtMode)


class Material(core.ResData):
    """Represents an FMAT subsection of a Model subfile, storing information
    on with which textures and how technically a surface is drawn.
    """
    _SIGNATURE = "FMAT"

    def __init__(self):

        self.name = ""
        self.flags = MaterialFlags.VISIBLE

        self.shader_assign = ShaderAssign()

        self.renderinfos: ResDict[RenderInfo] = ResDict()
        self.texture_refs: list[TextureRef] = []
        self.samplers: ResDict[Sampler] = ResDict()
        self.userdata: ResDict[UserData] = ResDict()
        self.shaderparams: ResDict[ShaderParam] = ResDict()

        self.shaderparamdata = bytearray()
        self.volatileflags = bytearray()

        self.render_state: RenderState
        self.renderinfo_size: int

        self.texture_slot_array: tuple[int, ...]
        self.sampler_slot_array: tuple[int, ...]
        self.param_idxs: tuple[int, ...]

    def __repr__(self) -> str:
        return "Material" + "{" + self.name + "}"

    @property
    def visible(self):
        return MaterialFlags.VISIBLE == self.flags

    @visible.setter
    def visible(self, value):
        if (value):
            self.flags |= MaterialFlags.VISIBLE
        else:
            self.flags = MaterialFlags.NONE

    def __fill_slots(self, count):
        slots = []
        for i in range(count):
            slots[i] = -1
        return slots

    def load(self, loader: core.ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        if (loader.is_switch):
            from ..switch.model import MaterialParser
            MaterialParser.load(loader, self)
        else:
            self.name = loader.load_string()
            self.flags = MaterialFlags(loader.read_uint32())
            idx = loader.read_uint16()
            num_renderinfo = loader.read_uint16()
            num_sampler = loader.read_byte()
            num_tex_ref = loader.read_byte()
            num_shaderparam = loader.read_uint16()
            num_shaderparamVolatile = loader.read_uint16()
            siz_param_source = loader.read_uint16()
            siz_param_raw = loader.read_uint16()
            num_user_data = loader.read_uint16()
            self.renderinfos = loader.load_dict(RenderInfo)
            self.render_state = loader.load(RenderState)
            self.shader_assign = loader.load(ShaderAssign)
            self.texture_refs = loader.load_list(TextureRef, num_tex_ref)
            ofs_sample_list = loader.read_offset()  # Only use dict.
            self.samplers = loader.load_dict(Sampler)
            ofs_shaderparam_list = loader.read_offset()  # Only use dict.
            self.shaderparams = loader.load_dict(ShaderParam)
            self.shaderparamdata = loader.load_custom(
                bytes, lambda: loader.read_bytes(siz_param_source)
            )
            self.userdata = loader.load_dict(UserData)
            self.volatileflags = loader.load_custom(
                bytearray,
                lambda: loader.read_bytes(math.ceil(num_shaderparam / 8.0))
            )
            user_pointer = loader.read_uint32()

        self.__read_shaderparams(self.shaderparamdata,
                                 '<' if loader.is_switch else '>')

    def __read_shaderparams(self, data: bytes, endianness: str):
        if (data is None):
            return
        import io
        with BinaryReader(io.BytesIO(data)) as reader:
            reader.endianness = endianness
            for param in self.shaderparams.values():
                reader.seek(param.data_offs, io.SEEK_SET)
                param.data = self.__read_param_data(param.type, reader)

    def __read_param_data(self, type_, reader: BinaryReader):
        match (type_):
            case ShaderParamType.BOOL: return reader.read_bool()
            case ShaderParamType.BOOL2: return reader.read_bools(2)
            case ShaderParamType.BOOL3: return reader.read_bools(3)
            case ShaderParamType.BOOL4: return reader.read_bools(4)
            case ShaderParamType.FLOAT: return reader.read_single()
            case ShaderParamType.FLOAT2: return reader.read_singles(2)
            case ShaderParamType.FLOAT2X2: return reader.read_singles(2 * 2)
            case ShaderParamType.FLOAT2X3: return reader.read_singles(2 * 3)
            case ShaderParamType.FLOAT2X4: return reader.read_singles(2 * 4)
            case ShaderParamType.FLOAT3: return reader.read_singles(3)
            case ShaderParamType.FLOAT3X2: return reader.read_singles(3 * 2)
            case ShaderParamType.FLOAT3X3: return reader.read_singles(3 * 3)
            case ShaderParamType.FLOAT3X4: return reader.read_singles(3 * 4)
            case ShaderParamType.FLOAT4: return reader.read_singles(4)
            case ShaderParamType.FLOAT4X2: return reader.read_singles(4 * 2)
            case ShaderParamType.FLOAT4X3: return reader.read_singles(4 * 3)
            case ShaderParamType.FLOAT4X4: return reader.read_singles(4 * 4)
            case ShaderParamType.INT: return reader.read_int32()
            case ShaderParamType.INT2: return reader.read_int32s(2)
            case ShaderParamType.INT3: return reader.read_int32s(3)
            case ShaderParamType.INT4: return reader.read_int32s(4)
            case ShaderParamType.UINT: return reader.read_int32()
            case ShaderParamType.UINT2: return reader.read_int32s(2)
            case ShaderParamType.UINT3: return reader.read_int32s(3)
            case ShaderParamType.UINT4: return reader.read_int32s(4)
            case ShaderParamType.RESERVED2: return reader.read_bytes(2)
            case ShaderParamType.RESERVED3: return reader.read_bytes(3)
            case ShaderParamType.RESERVED4: return reader.read_bytes(4)
            case ShaderParamType.SRT2D:
                return Srt2D(reader.read_vector2f(),
                             reader.read_single(),
                             reader.read_vector2f())
            case ShaderParamType.SRT3D:
                return Srt3D(reader.read_vector3f(),
                             reader.read_vector3f(),
                             reader.read_vector3f(),
                             )
            case ShaderParamType.TEX_SRT | ShaderParamType.TEX_SRT_EX:
                return TexSrt(TexSrtMode(reader.read_int32()),
                              reader.read_vector2f(),
                              reader.read_single(),
                              reader.read_vector2f())
        return 0


class MaterialFlags(IntEnum):
    """Represents general flags specifying how a Material is rendered."""
    # uint32

    NONE = 0
    """The material is not rendered at all."""

    VISIBLE = 1
    """The material is rendered."""


class ShaderAssign(core.ResData):
    def __init__(self):
        self.shader_archive_name: str = ''
        self.shading_model_name: str = ''
        self.revision = 0
        self.attrib_assigns: ResDict[ResString] = ResDict()
        self.sampler_assigns: ResDict[ResString] = ResDict()
        self.shaderoptions: ResDict[ResString] = ResDict()

    @property
    def shaderoptions_list(self):
        strings = []
        for option in self.shaderoptions:
            strings.append(self.ResStringDisplay(option.key, option.value))
        return strings

    @shaderoptions_list.setter
    def shaderoptions_list(self, value):
        self.shaderoptions.clear()
        for option in value:
            self.shaderoptions.append(option.name, option.value)

    class ResStringDisplay:
        def __init__(self, name=None, value=None):
            self.name = name
            self.value = value

    def load(self, loader: core.ResFileLoader):
        self.shader_archive_name = loader.load_string()
        self.shading_model_name = loader.load_string()

        if (loader.is_switch):
            self.attrib_assigns = loader.load_dict_values(ResString)
            self.sampler_assigns = loader.load_dict_values(ResString)
            self.shaderoptions = loader.load_dict_values(ResString)
            self.revision = loader.read_uint32()
            num_attrib_assign = loader.read_byte()
            num_sampler_assign = loader.read_byte()
            num_shaderoption = loader.read_uint16()
        else:
            self.revision = loader.read_uint32()
            num_attrib_assign = loader.read_byte()
            num_sampler_assign = loader.read_byte()
            num_shaderoption = loader.read_uint16()
            self.attrib_assigns = loader.load_dict(ResString)
            self.sampler_assigns = loader.load_dict(ResString)
            self.shaderoptions = loader.load_dict(ResString)


class RenderInfoType(IntEnum):
    """Represents the data type of elements of the RenderInfo value array."""
    # byte
    INT32 = 0
    SINGLE = 1
    STRING = 2


class RenderInfo(core.ResData):
    """Represents a render info in a FMAT section storing uniform parameters
    required to render the UserData"""

    def __init__(self):
        self.__value: tuple[Any, ...]
        self.type: RenderInfoType

        self.name = ""
        self.set_value([])

    @property
    def data(self):
        return self.__value

    @data.setter
    def data(self, value):
        self.__value = value

    def get_value_int32s(self) -> tuple[int, ...]:
        """Gets the stored value as an array."""
        if (self.__value is None):
            return tuple()
        return tuple(self.__value)

    def get_value(self) -> tuple[object, ...]:
        """Gets the stored value as an array."""
        if (self.__value is None):
            return tuple()
        return tuple(self.__value)

    def get_value_strings(self) -> tuple[str, ...]:
        if (self.__value is None or self.type != RenderInfoType.STRING):
            return ('',)
        return tuple(self.__value)

    def set_value(self, value):
        if (len(value) == 0 or isinstance(value[0], int)):
            self.type = RenderInfoType.INT32
        elif (isinstance(value[0], float)):
            self.type = RenderInfoType.SINGLE
        elif (isinstance(value[0], str)):
            self.type = RenderInfoType.STRING
        self.__value = value

    def load(self, loader: core.ResFileLoader):
        if (loader.is_switch):
            self.name = loader.load_string()
            data_offs = loader.read_offset()
            count = loader.read_uint16()
            self.type = RenderInfoType(loader.read_byte())
            loader.seek(5)

            match (self.type):
                case RenderInfoType.INT32:
                    self.__value = loader.load_custom(
                        tuple, lambda: loader.read_int32s(count), data_offs
                    )
                case RenderInfoType.SINGLE:
                    self.__value = loader.load_custom(
                        tuple, lambda: loader.read_singles(count), data_offs
                    )
                case RenderInfoType.STRING:
                    if (data_offs == 0):       # Some games have empty data
                        self.__value = ('',)   # offset and no strings
                    else:
                        self.__value = loader.load_custom(
                            tuple,
                            lambda: loader.load_strings(count), data_offs
                        )
        else:
            count = loader.read_uint16()
            self.type = RenderInfoType(loader.read_byte())
            loader.seek(1)
            self.name = loader.load_string()
            match (self.type):
                case RenderInfoType.INT32:
                    self.__value = loader.read_int32s(count)
                case RenderInfoType.SINGLE:
                    self.__value = loader.read_singles(count)
                case RenderInfoType.STRING:
                    self.__value = loader.load_strings(count)

    def read_data(self, loader: core.ResFileLoader,
                  typ: RenderInfoType, count):
        self.type = typ
        match (self.type):
            case RenderInfoType.INT32:
                self.__value = loader.read_int32s(count)
            case RenderInfoType.SINGLE:
                self.__value = loader.read_singles(count)
            case RenderInfoType.STRING:
                self.__value = loader.load_strings(count)


class RenderState(core.ResData):
    """Represents GX2 GPU configuration to determine how polygons are
    rendered.
    """

    def __init__(self):
        self.flags_mode = RenderStateFlagsMode.OPAQUE
        self.flags_blend_mode = RenderStateFlagsBlendMode.NONE

        # TODO I think this is wii U only


class RenderStateFlagsMode(IntEnum):
    # uint32
    CUSTOM = 0
    OPAQUE = 1
    ALPHA_MASK = 2
    TRANSLUCENT = 3


class RenderStateFlagsBlendMode(IntEnum):
    # uint32
    NONE = 0
    COLOR = 1
    LOGICAL = 2


class ShaderParam(core.ResData):
    """Represents a parameter value in a UserData section, passing data to
    shader variables"""

    def __init__(self):
        self.data: object
        self.callback_pointer: int
        self.use_padding: bool
        self.padding_length: int

        self.name = ""
        self.type = ShaderParamType.FLOAT
        self.data_offs = 0
        self.depended_idx = 0
        self.depend_idx = 0

    def __repr__(self):
        return "ShaderParam{" + str(self.name) + "}"

    @property
    def data_size(self):
        """The size of the value in bytes."""
        if (int(self.type) <= int(ShaderParamType.FLOAT4X4)):
            return 4 * (self.type.value & 0x03) + 1
        if (int(self.type) <= int(ShaderParamType.FLOAT4X4)):
            cols = (int(self.type) & 0x03) + 1
            rows = (int(self.type) - int(ShaderParamType.RESERVED2) >> 2) + 2
            return 4 * cols * rows

        # XXX this is supposed to use "sizeof" but python variables dont have
        # fixed sizes
        match self.type:
            case ShaderParamType.SRT2D:
                return 20
            case ShaderParamType.SRT3D:
                return 36
            case ShaderParamType.TEX_SRT:
                return 24
            case ShaderParamType.TEX_SRT_EX:
                return 28
        raise ValueError(
            f"Cannot retrieve size of unknown {self.type.name}")

    def load(self, loader: core.ResFileLoader):
        if (loader.is_switch):
            self.callback_pointer = loader.read_uint64()
            self.name = loader.load_string()
            self.type = ShaderParamType(loader.read_byte())
            siz_data = loader.read_byte()
            self.data_offs = loader.read_uint16()
            self.offset = loader.read_int32()  # Uniform variable offset
            self.depended_idx = loader.read_uint16()
            self.depend_idx = loader.read_uint16()
            padding2 = loader.read_uint32()  # Uniform variable offset.
        else:
            self.type = ShaderParamType(loader.read_byte())
            siz_data = loader.read_byte()

            if (siz_data != self.data_size and siz_data > self.data_size):
                self.use_padding = True
                self.padding_length = siz_data - self.data_size

            self.data_offs = loader.read_uint16()
            self.offset = loader.read_int32()  # Uniform variable offset.
            if (loader.res_file.version >= 0x03040000):
                self.callback_pointer = loader.read_uint32()
                self.depended_idx = loader.read_uint16()
                self.depend_idx = loader.read_uint16()
            elif (loader.res_file.version >= 0x03030000
                  and loader.res_file.version < 0x03040000):
                self.callback_pointer = loader.read_uint32()
                self.depended_idx = loader.read_uint16()
                self.depend_idx = loader.read_uint16()
                fmat_offset = loader.read_uint32()  # Why does this have this?
            self.name = loader.load_string()


class ShaderParamType(IntEnum):
    """Represents the data types in which ShaderParam instances can store their
    value.
    """
    # byte

    BOOL = 0
    """The value is a single Boolean."""

    BOOL2 = auto()
    """The value is a Vector2Bool."""

    BOOL3 = auto()
    """The value is a Vector3Bool."""

    BOOL4 = auto()
    """The value is a Vector4Bool."""

    INT = auto()
    """The value is a single Int32."""

    INT2 = auto()
    """The value is a Vector2."""

    INT3 = auto()
    """The value is a Vector3."""

    INT4 = auto()
    """The value is a Vector4."""

    UINT = auto()
    """The value is a single UInt32."""

    UINT2 = auto()
    """The value is a Vector2U."""

    UINT3 = auto()
    """The value is a Vector3U."""

    UINT4 = auto()
    """The value is a Vector4U."""

    FLOAT = auto()
    """The value is a single Single."""

    FLOAT2 = auto()
    """The value is a Vector2F."""

    FLOAT3 = auto()
    """The value is a Vector3F."""

    FLOAT4 = auto()
    """The value is a Vector4F."""

    RESERVED2 = auto()
    """An invalid type for ShaderParam values,
    only used for internal computations.
    """

    FLOAT2X2 = auto()
    """The value is a Matrix2."""

    FLOAT2X3 = auto()
    """The value is a Matrix2x3."""

    FLOAT2X4 = auto()
    """The value is a Matrix2x4."""

    RESERVED3 = auto()
    """An invalid type for ShaderParam values,
    only used for internal computations.
    """

    FLOAT3X2 = auto()
    """The value is a Matrix3x2."""

    FLOAT3X3 = auto()
    """The value is a Matrix3."""

    FLOAT3X4 = auto()
    """The value is a Matrix3x4."""

    RESERVED4 = auto()
    """An invalid type for ShaderParam values,
    only used for internal computations.
    """

    FLOAT4X2 = auto()
    """The value is a Single."""

    FLOAT4X3 = auto()
    """The value is a Matrix4x3."""

    FLOAT4X4 = auto()
    """The value is a Matrix4."""

    SRT2D = auto()
    """The value is a Srt2D."""

    SRT3D = auto()
    """The value is a Srt3D."""

    TEX_SRT = auto()
    """The value is a TexSrt."""

    TEX_SRT_EX = auto()
    """The value is a TexSrtEx."""


class Sampler(core.ResData):
    """Represents a Texture sampler in a UserData section, storing
    configuration on how to draw and interpolate textures.
    """

    def __init__(self):
        self.tex_sampler: TexSampler
        self.name: str

    def __repr__(self):
        return "Sampler{" + str(self.name) + "}"

    def load(self, loader: core.ResFileLoader):
        if (loader.is_switch):
            from ..switch import model
            sampler = model.SamplerSwitch()
            sampler.load(loader)
            self.tex_sampler = sampler.to_tex_sampler()
        else:
            self.tex_sampler = TexSampler(loader.read_int32s(3))
            handle = loader.read_uint32()
            self.name = loader.load_string()
            idx = loader.read_byte()
            loader.seek(3)

    class MaxAnisotropic(IntEnum):
        # byte
        RATIO_1_1 = 0x1
        RATIO_2_1 = 0x2
        RATIO_4_1 = 0x4
        RATIO_8_1 = 0x8
        RATIO_16_1 = 0x10

    # uint16
    class MipFilterModes(IntEnum):
        NONE = 0
        POINTS = 1
        LINEAR = 2

    # uint16
    class ExpandFilterModes(IntEnum):
        POINTS = 1 << 2
        LINEAR = 2 << 2

    # uint16
    class ShrinkFilterModes(IntEnum):
        POINTS = 1 << 4
        LINEAR = 2 << 4

    class CompareFunction(IntEnum):
        """Represents compare functions used for depth and stencil tests."""
        # byte
        NEVER = 0
        LESS = 1
        EQUAL = 2
        LESS_OR_EQUAL = 3
        GREATER = 4
        NOT_EQUAL = 5
        GREATER_OR_EQUAL = 6
        ALWAYS = 7

    class TexBorderType(IntEnum):
        """Represents type of border color to use."""
        # byte
        WHITE = 0
        TRANSPARENT = 1
        OPAQUE = 2

    # sbyte
    class TexClamp(IntEnum):
        """Represents how to treat texture coordinates outside of the
        normalized coordinate texture range.
        """
        REPEAT = 0
        MIRROR = 1
        CLAMP = 2
        CLAMP_TO_EDGE = 3
        MIRROR_ONCE = 4
        MIRROR_ONCE_CLAMP_TO_EDGE = 5

# Included in GX2, and not Material


class TexSampler:
    """Represents a GX2 texture sampler controlling how a texture is sampled
    and drawn onto a surface."""
    __CLAMP_X_BIT = 0
    __CLAMP_X_BITS = 3
    __CLAMP_Y_BIT = 3
    __CLAMP_Y_BITS = 3
    __CLAMP_Z_BIT = 6
    __CLAMP_Z_BITS = 3
    __XY_MAG_FILTER_BIT = 9
    __XY_MAG_FILTER_BITS = 2
    __XY_MIN_FILTER_BIT = 12
    __XY_MIN_FILTER_BITS = 2
    __Z_FILTER_BIT = 15
    __Z_FILTER_BITS = 2
    __MIP_FILTER_BIT = 17
    __MIP_FILTER_BITS = 2
    __MAX_ANISOTROPIC_RATIO_BIT = 19
    __MAX_ANISOTROPIC_RATIO_BITS = 3
    __BORDER_TYPE_BIT = 22
    __BORDER_TYPE_BITS = 2
    __DEPTH_COMPARE_FUNC_BIT = 26
    __DEPTH_COMPARE_FUNC_BITS = 3

    __MIN_LOD_BIT = 0
    __MIN_LOD_BITS = 10
    __MAX_LOD_BIT = 10
    __MAX_LOD_BITS = 10
    __LOD_BIAS_BIT = 20
    __LOD_BIAS_BITS = 12

    __DEPTH_COMPARE_BIT = 30

    def __init__(self, values=None):
        self.__filter_flags: int
        if (values):
            self.values = values
        else:
            self.values = [33559049, 851968, 2147483648]

            self.clamp_x = gx2.GX2TexClamp.WRAP
            self.clamp_y = gx2.GX2TexClamp.WRAP
            self.clamp_z = gx2.GX2TexClamp.CLAMP
            self.mag_filter = gx2.GX2TexXYFilterType.BILINEAR
            self.min_filter = gx2.GX2TexXYFilterType.BILINEAR
            self.z_filter = gx2.GX2TexZFilterType.LINEAR
            self.mip_filter = gx2.GX2TexMipFilterType.LINEAR
            self.max_anisotropic_ratio = gx2.GX2TexAnisoRatio.RATIO_1_1
            self.border_type = gx2.GX2TexBorderType.CLEAR_BLACK
            self.depth_compare_func = gx2.GX2CompareFunction.NEVER
            self.lod_bias = 0
            self.min_lod = 0
            self.max_lod = 13

    @property
    def clamp_x(self):
        """The texture repetition mode on the X axis."""
        return gx2.GX2TexClamp(
            core._decode(self.values[0],
                         self.__CLAMP_X_BIT,
                         self.__CLAMP_X_BITS))

    @clamp_x.setter
    def clamp_x(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__CLAMP_X_BIT,
                                      self.__CLAMP_X_BITS)

    @property
    def clamp_y(self):
        """The texture repetition mode on the Y axis."""
        return gx2.GX2TexClamp(
            core._decode(self.values[0],
                         self.__CLAMP_Y_BIT,
                         self.__CLAMP_Y_BITS))

    @clamp_y.setter
    def clamp_y(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__CLAMP_Y_BIT,
                                      self.__CLAMP_Y_BITS)

    @property
    def clamp_z(self):
        """The texture repetition mode on the Z axis."""
        return gx2.GX2TexClamp(
            core._decode(self.values[0],
                         self.__CLAMP_Z_BIT,
                         self.__CLAMP_Z_BITS))

    @clamp_z.setter
    def clamp_z(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__CLAMP_Z_BIT,
                                      self.__CLAMP_Z_BITS)

    @property
    def mag_filter(self):
        """The texture filtering on the X and Y axes when the texture is drawn
        larger than the actual texture's resolution.
        """
        return gx2.GX2TexXYFilterType(
            core._decode(self.values[0],
                         self.__XY_MAG_FILTER_BIT,
                         self.__XY_MAG_FILTER_BITS))

    @mag_filter.setter
    def mag_filter(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__XY_MAG_FILTER_BIT,
                                      self.__XY_MAG_FILTER_BITS)

    @property
    def min_filter(self):
        """The texture filtering on the X and Y axes when the texture is drawn
        smaller than the actual texture's resolution.
        """
        return gx2.GX2TexXYFilterType(
            core._decode(self.values[0],
                         self.__XY_MIN_FILTER_BIT,
                         self.__XY_MIN_FILTER_BITS))

    @min_filter.setter
    def min_filter(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__XY_MIN_FILTER_BIT,
                                      self.__XY_MIN_FILTER_BITS)

    @property
    def z_filter(self):
        """The texture filtering on the Z axis."""
        return gx2.GX2TexZFilterType(
            core._decode(self.values[0],
                         self.__Z_FILTER_BIT,
                         self.__Z_FILTER_BITS))

    @z_filter.setter
    def z_filter(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__Z_FILTER_BIT,
                                      self.__Z_FILTER_BITS)

    @property
    def mip_filter(self):
        """The texture filtering for mipmaps."""
        return gx2.GX2TexMipFilterType(
            core._decode(self.values[0],
                         self.__MIP_FILTER_BIT,
                         self.__MIP_FILTER_BITS))

    @mip_filter.setter
    def mip_filter(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__MIP_FILTER_BIT,
                                      self.__MIP_FILTER_BITS)

    @property
    def max_anisotropic_ratio(self):
        """The maximum anisotropic filtering level to use."""
        return gx2.GX2TexAnisoRatio(
            core._decode(self.values[0],
                         self.__MAX_ANISOTROPIC_RATIO_BIT,
                         self.__MAX_ANISOTROPIC_RATIO_BITS))

    @max_anisotropic_ratio.setter
    def max_anisotropic_ratio(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__MAX_ANISOTROPIC_RATIO_BIT,
                                      self.__MAX_ANISOTROPIC_RATIO_BITS)

    @property
    def border_type(self):
        """Qhat color to draw at places not reached by a texture if the clamp
        mode does not repeat it.
        """
        return gx2.GX2TexBorderType(
            core._decode(self.values[0],
                         self.__BORDER_TYPE_BIT,
                         self.__BORDER_TYPE_BITS))

    @border_type.setter
    def border_type(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__BORDER_TYPE_BIT,
                                      self.__BORDER_TYPE_BITS)

    @property
    def depth_compare_func(self):
        """The depth comparison function"""
        return gx2.GX2CompareFunction(
            core._decode(self.values[0],
                         self.__DEPTH_COMPARE_FUNC_BIT,
                         self.__DEPTH_COMPARE_FUNC_BITS))

    @depth_compare_func.setter
    def depth_compare_func(self, value):
        self.values[0] = core._encode(self.values[0],
                                      value,
                                      self.__DEPTH_COMPARE_FUNC_BIT,
                                      self.__DEPTH_COMPARE_FUNC_BITS)

    @property
    def min_lod(self):
        """The minimum LoD level."""
        return self.__usingle_4x6_to_single(
            core._decode(self.values[1],
                         self.__MIN_LOD_BIT,
                         self.__MIN_LOD_BITS))

    @min_lod.setter
    def min_lod(self, value):
        self.values[1] = core._encode(self.values[1],
                                      self.__single_to_usingle4x6(value),
                                      self.__MIN_LOD_BIT,
                                      self.__MIN_LOD_BITS)

    @property
    def max_lod(self):
        """The maximum LoD level."""
        return self.__usingle_4x6_to_single(
            core._decode(self.values[1],
                         self.__MAX_LOD_BIT,
                         self.__MAX_LOD_BITS))

    @max_lod.setter
    def max_lod(self, value):
        self.values[1] = core._encode(self.values[1],
                                      self.__single_to_usingle4x6(value),
                                      self.__MAX_LOD_BIT,
                                      self.__MAX_LOD_BITS)

    @property
    def lod_bias(self):
        """The LoD bias."""  # helpful
        return self.__single_5x6_to_single(
            core._decode(self.values[1],
                         self.__LOD_BIAS_BIT,
                         self.__LOD_BIAS_BITS))

    @lod_bias.setter
    def lod_bias(self, value):
        self.values[1] = core._encode(self.values[1],
                                      self.__single_to_single5x6(value),
                                      self.__LOD_BIAS_BIT,
                                      self.__LOD_BIAS_BITS)

    @property
    def depth_compare_enabled(self):
        """A value indicating whether depth comparison is enabled 
        (never set for a real console).
        """
        return core.get_bit(self.values[2], self.__DEPTH_COMPARE_BIT)

    @depth_compare_enabled.setter
    def depth_compare_enabled(self, value: bool):
        self.values[2] = core.set_bit(self.values[2],
                                      self.__DEPTH_COMPARE_BIT,
                                      value)

    # Private Methods

    def __single_5x6_to_single(self, value: int):

        # Use a signed value to get arithmetic right shifts to receive correct
        # negative numbers.
        signed = (value << 20) & 0xFFFFFFFF  # XXX no idea if this is right
        return (signed >> 20) / float(64)

    def __usingle_4x6_to_single(self, value: int):
        return value / float(64)

    def __single_to_single5x6(self, value: float):
        if (value <= -32):
            return 32 * 64
        elif (value >= 31.984375):
            return 31.984375 * 64
        return value * 64

    def __single_to_usingle4x6(self, value: float):
        if (value <= 0):
            return 0
        elif (value >= 13):
            return 13 * 64
        return int(value * 64)
