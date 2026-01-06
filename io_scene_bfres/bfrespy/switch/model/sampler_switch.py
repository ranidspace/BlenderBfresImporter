from enum import IntEnum
from ... import core
from ... import models
from ... import gx2


class SamplerSwitch(core.ResData):
    __FLAGS_SHRINK_MASK = 0b00000000_00110000
    __FLAGS_EXPAND_MASK = 0b00000000_00001100
    __FLAGS_MIPMAP_MASK = 0b00000000_00000011

    def __init__(self):
        self.wrapmode_u = self.TexClamp.REPEAT
        self.wrapmode_v = self.TexClamp.REPEAT
        self.wrapmode_w = self.TexClamp.CLAMP
        self.compare_func = self.CompareFunction.NEVER
        self.border_color_type = self.TexBorderType.WHITE
        self.anisotropic = self.MaxAnisotropic.RATIO_1_1
        self.lod_bias = 0.0
        self.min_lod = 0.0
        self.max_lod = 13.0
        self.__filter_flags = 42

    # Properties

    @property
    def shrink_xy(self):
        """The texture filtering on the X and Y axes when the texture is drawn
        smaller than the actual texture's resolution.
        """
        return self.ShrinkFilterModes(self.__filter_flags
                                      & self.__FLAGS_SHRINK_MASK)

    @shrink_xy.setter
    def shrink_xy(self, value):
        self.__filter_flags = (self.__filter_flags
                               & ~self.__FLAGS_SHRINK_MASK
                               | int(value))

    @property
    def expand_xy(self):
        """The texture filtering on the X and Y axes when the texture is drawn
        larger than the actual texture's resolution.
        """
        return self.ExpandFilterModes(self.__filter_flags
                                      & self.__FLAGS_EXPAND_MASK)

    @expand_xy.setter
    def expand_xy(self, value):
        self.__filter_flags = (self.__filter_flags
                               & ~self.__FLAGS_EXPAND_MASK
                               | int(value))

    @property
    def mipmap(self):
        """The texture filtering for mipmaps."""
        return self.MipFilterModes(self.__filter_flags
                                   & self.__FLAGS_MIPMAP_MASK)

    @mipmap.setter
    def mipmap(self, value):
        self.__filter_flags = (self.__filter_flags
                               & ~self.__FLAGS_MIPMAP_MASK
                               | int(value))

    # Methods

    def to_tex_sampler(self):
        sampler = models.TexSampler()
        sampler.__filter_flags = self.__filter_flags

        if (self.wrapmode_u in self.clamp_modes):
            sampler.clamp_x = self.clamp_modes[self.wrapmode_u]
        if (self.wrapmode_v in self.clamp_modes):
            sampler.clamp_y = self.clamp_modes[self.wrapmode_v]
        if (self.wrapmode_w in self.clamp_modes):
            sampler.clamp_z = self.clamp_modes[self.wrapmode_w]
        if (self.anisotropic in self.anisotropic_modes):
            sampler.max_anisotropic_ratio = self.anisotropic_modes[self.anisotropic]
        if (self.compare_func in self.compare_modes):
            sampler.depth_compare_func = self.compare_modes[self.compare_func]
        if (self.border_color_type in self.border_modes):
            sampler.border_type = self.border_modes[self.border_color_type]

        if (self.mipmap in self.mip_filters):
            sampler.mip_filter = self.mip_filters[self.mipmap]
        if (self.expand_xy in self.expand_filters):
            sampler.mag_filter = self.expand_filters[self.expand_xy]
        if (self.shrink_xy in self.shrink_filters):
            sampler.min_filter = self.shrink_filters[self.shrink_xy]

        sampler.max_lod = self.max_lod
        sampler.min_lod = self.min_lod
        sampler.lod_bias = self.lod_bias

        return sampler

    def load(self, loader: core.ResFileLoader):
        self.wrapmode_u = self.TexClamp(loader.read_byte())
        self.wrapmode_v = self.TexClamp(loader.read_byte())
        self.wrapmode_w = self.TexClamp(loader.read_byte())
        self.compare_func = self.CompareFunction(loader.read_byte())
        self.border_color_type = self.TexBorderType(loader.read_byte())
        self.anisotropic = self.MaxAnisotropic(loader.read_byte())
        self.__filter_flags = loader.read_uint16()
        self.min_lod = loader.read_single()
        self.max_lod = loader.read_single()
        self.lod_bias = loader.read_single()
        loader.seek(12)

    class MaxAnisotropic(IntEnum):
        # byte
        RATIO_1_1 = 0x1
        RATIO_2_1 = 0x2
        RATIO_4_1 = 0x4
        RATIO_8_1 = 0x8
        RATIO_16_1 = 0x10

    class MipFilterModes(IntEnum):
        # uint16
        NONE = 0
        POINTS = 1
        LINEAR = 2

    class ExpandFilterModes(IntEnum):
        # uint16
        POINTS = 1 << 2
        LINEAR = 2 << 2

    class ShrinkFilterModes(IntEnum):
        # uint16
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

    class TexClamp(IntEnum):
        """Represents how to treat texture coordinates outside of the
        normalized coordinate texture range.
        """
        # sbyte
        REPEAT = 0
        MIRROR = 1
        CLAMP = 2
        CLAMP_TO_EDGE = 3
        MIRROR_ONCE = 4
        MIRROR_ONCE_CLAMP_TO_EDGE = 5

    expand_filters = {
        ExpandFilterModes.LINEAR: gx2.GX2TexXYFilterType.BILINEAR,
        ExpandFilterModes.POINTS: gx2.GX2TexXYFilterType.POINT,
    }

    shrink_filters = {
        ShrinkFilterModes.LINEAR: gx2.GX2TexXYFilterType.BILINEAR,
        ShrinkFilterModes.POINTS: gx2.GX2TexXYFilterType.POINT,
    }

    mip_filters = {
        MipFilterModes.LINEAR: gx2.GX2TexMipFilterType.LINEAR,
        MipFilterModes.POINTS: gx2.GX2TexMipFilterType.POINT,
        MipFilterModes.NONE: gx2.GX2TexMipFilterType.NO_MIP,
    }

    border_modes = {
        TexBorderType.OPAQUE: gx2.GX2TexBorderType.SOLID_BLACK,
        TexBorderType.WHITE: gx2.GX2TexBorderType.SOLID_WHITE,
        TexBorderType.TRANSPARENT: gx2.GX2TexBorderType.CLEAR_BLACK,
    }

    compare_modes = {
        CompareFunction.ALWAYS: gx2.GX2CompareFunction.ALWAYS,
        CompareFunction.EQUAL: gx2.GX2CompareFunction.EQUAL,
        CompareFunction.GREATER: gx2.GX2CompareFunction.GREATER,
        CompareFunction.GREATER_OR_EQUAL: gx2.GX2CompareFunction.GREATER_OR_EQUAL,
        CompareFunction.LESS: gx2.GX2CompareFunction.LESS,
        CompareFunction.LESS_OR_EQUAL: gx2.GX2CompareFunction.LESS_OR_EQUAL,
        CompareFunction.NEVER: gx2.GX2CompareFunction.NEVER,
        CompareFunction.NOT_EQUAL: gx2.GX2CompareFunction.NOT_EQUAL,
    }

    clamp_modes = {
        TexClamp.REPEAT: gx2.GX2TexClamp.WRAP,
        TexClamp.MIRROR: gx2.GX2TexClamp.MIRROR,
        TexClamp.MIRROR_ONCE: gx2.GX2TexClamp.MIRROR_ONCE,
        TexClamp.MIRROR_ONCE_CLAMP_TO_EDGE: gx2.GX2TexClamp.MIRROR_ONCE_BORDER,
        TexClamp.CLAMP: gx2.GX2TexClamp.CLAMP,
        TexClamp.CLAMP_TO_EDGE: gx2.GX2TexClamp.CLAMP_BORDER,
    }

    anisotropic_modes = {
        MaxAnisotropic.RATIO_1_1: gx2.GX2TexAnisoRatio.RATIO_1_1,
        MaxAnisotropic.RATIO_2_1: gx2.GX2TexAnisoRatio.RATIO_2_1,
        MaxAnisotropic.RATIO_4_1: gx2.GX2TexAnisoRatio.RATIO_4_1,
        MaxAnisotropic.RATIO_8_1: gx2.GX2TexAnisoRatio.RATIO_8_1,
        MaxAnisotropic.RATIO_16_1: gx2.GX2TexAnisoRatio.RATIO_16_1,
    }
