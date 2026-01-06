from enum import IntEnum, IntFlag


class GX2AAMode(IntEnum):
    """Represents the AA modes (number of samples) for a surface."""
    MODE1X = 0
    MODE2X = 1
    MODE4X = 2
    MODE8X = 3


class GX2AttribType(IntEnum):
    """Represents the read format of a vertex attribute entry"""
    GX2_ATTRIB_TYPE_8 = 0x00
    GX2_ATTRIB_TYPE_4_4 = 0x01
    GX2_ATTRIB_TYPE_16 = 0x02
    GX2_ATTRIB_TYPE_16_FLOAT = 0x03
    GX2_ATTRIB_TYPE_8_8 = 0x04
    GX2_ATTRIB_TYPE_32 = 0x05
    GX2_ATTRIB_TYPE_32_FLOAT = 0x06
    GX2_ATTRIB_TYPE_16_16 = 0x07
    GX2_ATTRIB_TYPE_16_16_FLOAT = 0x08
    GX2_ATTRIB_TYPE_10_11_11_FLOAT = 0x09
    GX2_ATTRIB_TYPE_8_8_8_8 = 0x0A
    GX2_ATTRIB_TYPE_10_10_10_2 = 0x0B
    GX2_ATTRIB_TYPE_32_32 = 0x0C
    GX2_ATTRIB_TYPE_32_32_FLOAT = 0x0D
    GX2_ATTRIB_TYPE_16_16_16_16 = 0x0E
    GX2_ATTRIB_TYPE_16_16_16_16_FLOAT = 0x0F
    GX2_ATTRIB_TYPE_32_32_32 = 0x10
    GX2_ATTRIB_TYPE_32_32_32_FLOAT = 0x11
    GX2_ATTRIB_TYPE_32_32_32_32 = 0x12
    GX2_ATTRIB_TYPE_32_32_32_32_FLOAT = 0x13


class GX2AttribFlag(IntFlag):
    """Represents the flags of a vertex attribute entry"""
    GX2_ATTRIB_FLAG_INTEGER = 0x100
    GX2_ATTRIB_FLAG_SIGNED = 0x200
    GX2_ATTRIB_FLAG_DEGAMMA = 0x400
    GX2_ATTRIB_FLAG_SCALED = 0x800


class GX2AttribFormat(IntEnum):
    """Represents the format of a vertex attribute entry"""
    # 8 bits (8 x 1)
    FORMAT_8_UNORM = 0X00000000
    FORMAT_8_UINT = 0X00000100
    FORMAT_8_SNORM = 0X00000200
    FORMAT_8_SINT = 0X00000300
    FORMAT_8_UINTTOSINGLE = 0X00000800
    FORMAT_8_SINTTOSINGLE = 0X00000A00
    # 8 bits (4 x 2)
    FORMAT_4_4_UNORM = 0x00000001
    # 16 bits (16 x 1)
    FORMAT_16_UNORM = 0X00000002
    FORMAT_16_UINT = 0X00000102
    FORMAT_16_SNORM = 0X00000202
    FORMAT_16_SINT = 0X00000302
    FORMAT_16_SINGLE = 0X00000803
    FORMAT_16_UINTTOSINGLE = 0X00000802
    FORMAT_16_SINTTOSINGLE = 0X00000A02
    # 16 bits (8 x 2)
    FORMAT_8_8_UNORM = 0X00000004
    FORMAT_8_8_UINT = 0X00000104
    FORMAT_8_8_SNORM = 0X00000204
    FORMAT_8_8_SINT = 0X00000304
    FORMAT_8_8_UINTTOSINGLE = 0X00000804
    FORMAT_8_8_SINTTOSINGLE = 0X00000A04
    # 32 bits (32 x 1)
    FORMAT_32_UINT = 0X00000105
    FORMAT_32_SINT = 0X00000305
    FORMAT_32_SINGLE = 0X00000806
    # 32 bits (16 x 2)
    FORMAT_16_16_UNORM = 0X00000007
    FORMAT_16_16_UINT = 0X00000107
    FORMAT_16_16_SNORM = 0X00000207
    FORMAT_16_16_SINT = 0X00000307
    FORMAT_16_16_SINGLE = 0X00000808
    FORMAT_16_16_UINTTOSINGLE = 0X00000807
    FORMAT_16_16_SINTTOSINGLE = 0X00000A07
    # 32 bits (10/11 x 3)
    FORMAT_10_11_11_SINGLE = 0X00000809
    # 32 bits (8 x 4)
    FORMAT_8_8_8_8_UNORM = 0X0000000A
    FORMAT_8_8_8_8_UINT = 0X0000010A
    FORMAT_8_8_8_8_SNORM = 0X0000020A
    FORMAT_8_8_8_8_SINT = 0X0000030A
    FORMAT_8_8_8_8_UINTTOSINGLE = 0X0000080A
    FORMAT_8_8_8_8_SINTTOSINGLE = 0X00000A0A
    # 32 bits (10 x 3 + 2)
    FORMAT_10_10_10_2_UNORM = 0X0000000B
    FORMAT_10_10_10_2_UINT = 0X0000010B
    FORMAT_10_10_10_2_SNORM = 0X0000020B  # High 2 bits are UNorm
    FORMAT_10_10_10_2_SINT = 0X0000030B
    # 64 bits (32 x 2)
    FORMAT_32_32_UINT = 0X0000010C
    FORMAT_32_32_SINT = 0X0000030C
    FORMAT_32_32_SINGLE = 0X0000080D
    # 64 bits (16 x 4)
    FORMAT_16_16_16_16_UNORM = 0X0000000E
    FORMAT_16_16_16_16_UINT = 0X0000010E
    FORMAT_16_16_16_16_SNORM = 0X0000020E
    FORMAT_16_16_16_16_SINT = 0X0000030E
    FORMAT_16_16_16_16_SINGLE = 0X0000080F
    FORMAT_16_16_16_16_UINTTOSINGLE = 0X0000080E
    FORMAT_16_16_16_16_SINTTOSINGLE = 0X00000A0E
    # 96 bits (32 x 3)
    FORMAT_32_32_32_UINT = 0X00000110
    FORMAT_32_32_32_SINT = 0X00000310
    FORMAT_32_32_32_SINGLE = 0X00000811
    # 128 bits (32 x 4){
    FORMAT_32_32_32_32_UINT = 0X00000112
    FORMAT_32_32_32_32_SINT = 0X00000312
    FORMAT_32_32_32_32_SINGLE = 0X00000813


class GX2BlendCombine(IntEnum):
    """Represents how the terms of the blend function are combined."""
    ADD = 0
    SOURCE_MINUS_DESTINATION = 1
    MINIMUM = 2
    MAXIMUM = 3
    DESTINATION_MINUS_SOURCE = 4


class GX2BlendFunction(IntEnum):
    """Represents the factors used in the blend function"""
    ZERO = 0
    ONE = 1
    SOURCE_COLOR = 2
    ONE_MINUS_SOURCE_COLOR = 3
    SOURCE_ALPHA = 4
    ONE_MINUS_SOURCE_ALPHA = 5
    DESTINATION_ALPHA = 6
    ONE_MINUS_DESTINATION_ALPHA = 7
    DESTINATION_COLOR = 8
    ONE_MINUS_DESTINATION_COLOR = 9
    SOURCE_ALPHA_SATURATE = 10
    CONSTANT_COLOR = 13
    ONE_MINUS_CONSTANT_COLOR = 14
    SOURCE1_COLOR = 15
    ONE_MINUS_SOURCE1_COLOR = 16
    SOURCE1_ALPHA = 17
    ONE_MINUS_SOURCE1_ALPHA = 18
    CONSTANT_ALPHA = 19
    ONE_MINUS_CONSTANT_ALPHA = 20


class GX2CompareFunction(IntEnum):
    """Represents compare functions used for depth and stencil tests."""
    NEVER = 0
    LESS = 1
    EQUAL = 2
    LESS_OR_EQUAL = 3
    GREATER = 4
    NOT_EQUAL = 5
    GREATER_OR_EQUAL = 6
    ALWAYS = 7


class GX2CompSel(IntEnum):
    """Represents the source channels to map to a color channel in textures."""
    CHANNELR = 0
    CHANNELG = 1
    CHANNELB = 2
    CHANNELA = 3
    ALWAYS0 = 4
    ALWAYS1 = 5


class GX2FrontFaceMode(IntEnum):
    """Represents the vertex order of front-facing polygons."""
    COUNTERCLOCKWISE = 0
    CLOCKWISE = 1


class GX2IndexFormat(IntEnum):
    """Represents the type in which vertex indices are stored."""
    UINT16_LITTLE_ENDIAN = 0
    UINT32_LITTLE_ENDIAN = 1
    UINT16 = 4
    UINT32 = 9


class GX2LogicOp(IntEnum):
    """Represents the logic op function to perform."""

    CLEAR = 0x00
    """Black"""

    SET = 0xFF
    """White"""

    COPY = 0xCC
    """Source (Default)"""

    INVERSE_COPY = 0x33
    """~Source"""

    NO_OPERATION = 0xAA
    """Destination"""

    INVERSE = 0x55
    """~Destination"""

    AND = 0x88
    """Source & Destination"""

    NAND = 0x77
    """~(Source & Destination)"""

    OR = 0xEE
    """Source | Destination"""

    NOR = 0x11
    """~(Source | Destination)"""

    XOR = 0x66
    """Source ^ Destination"""

    EQUIVALENT = 0x99
    """ ~(Source ^ Destination)"""

    REVERSE_AND = 0x44
    """Source & ~Destination"""

    INVERSE_AND = 0x22
    """~Source & Destination"""

    REVERSE_OR = 0xDD
    """Source | ~Destination"""

    INVERSE_OR = 0xBB
    """~Source | Destination"""


class GX2PolygonMode(IntEnum):
    """Represents the base primitive used to draw each side of the polygon
    when dual-sided polygon mode is enabled."""
    POINT = 0
    LINE = 1
    TRIANGLE = 2


class GX2PrimitiveType(IntEnum):
    """Represents the type of primitives to draw."""

    POINTS = 0x01
    """Requires at least 1 element and 1 more to draw another primitive."""

    LINES = 0x02
    """Requires at least 2 elements and 2 more to draw another primitive."""

    LINE_STRIP = 0x03
    """Requires at least 2 elements and 1 more to draw another primitive."""

    TRIANGLES = 0x04
    """Requires at least 3 elements and 3 more to draw another primitive."""

    TRIANGLE_FAN = 0x05
    """Requires at least 3 elements and 1 more to draw another primitive."""

    TRIANGLE_STRIP = 0x06
    """Requires at least 3 elements and 1 more to draw another primitive."""

    LINES_ADJACENCY = 0x0A
    """Requires at least 4 elements and 4 more to draw another primitive."""

    LINE_STRIP_ADJACENCY = 0x0B
    """Requires at least 4 elements and 1 more to draw another primitive."""

    TRIANGLES_ADJACENCY = 0x0C
    """Requires at least 6 elements and 6 more to draw another primitive."""

    TRIANGLE_STRIP_ADJACENCY = 0x0D
    """Requires at least 6 elements and 2 more to draw another primitive."""

    RECTS = 0x11
    """Requires at least 3 elements and 3 more to draw another primitive."""

    LINE_LOOP = 0x12
    """Requires at least 2 elements and 1 more to draw another primitive."""

    QUADS = 0x13
    """Requires at least 4 elements and 4 more to draw another primitive."""

    QUAD_STRIP = 0x14
    """Requires at least 4 elements and 2 more to draw another primitive."""

    TESSELLATE_LINES = 0x82
    """Requires at least 2 elements and 2 more to draw another primitive."""

    TESSELLATE_LINE_STRIP = 0x83
    """Requires at least 2 elements and 1 more to draw another primitive."""

    TESSELLATE_TRIANGLES = 0x84
    """Requires at least 3 elements and 3 more to draw another primitive."""

    TESSELLATE_TRIANGLE_STRIP = 0x86
    """Requires at least 3 elements and 1 more to draw another primitive."""

    TESSELLATE_QUADS = 0x93
    """Requires at least 4 elements and 4 more to draw another primitive."""

    TESSELLATE_QUAD_STRIP = 0x94
    """Requires at least 4 elements and 2 more to draw another primitive."""


class GX2StencilFunction(IntEnum):
    """Represents the stencil function to be performed if stencil tests pass."""
    KEEP = 0
    ZERO = 1
    REPLACE = 2
    INCREMENT = 3
    DECREMENT = 4
    INVERT = 5
    INCREMENT_WRAP = 6
    DECREMENT_WRAP = 7


class GX2SurfaceDim(IntEnum):
    """Represents shapes of a given surface or texture."""
    DIM1D = 0
    DIM2D = 1
    DIM3D = 2
    DIM_CUBE = 3
    DIM1D_ARRAY = 4
    DIM2D_ARRAY = 5
    DIM2D_MSAA = 6
    DIM2D_MSAA_ARRAY = 7


class GX2SurfaceFormat(IntEnum):
    """Represents desired texture, color-buffer, depth-buffer, or scan-buffer formats."""
    INVALID = 0X00000000
    TC_R8_UNORM = 0X00000001
    TC_R8_UINT = 0X00000101
    TC_R8_SNORM = 0X00000201
    TC_R8_SINT = 0X00000301
    T_R4_G4_UNORM = 0X00000002
    TCD_R16_UNORM = 0X00000005
    TC_R16_UINT = 0X00000105
    TC_R16_SNORM = 0X00000205
    TC_R10_G10_B10_A2_SNORM = 0X00000219
    TC_R10_G10_B10_A2_SINT = 0X00000319
    TCS_R8_G8_B8_A8_UNORM = 0X0000001A
    TC_R8_G8_B8_A8_UINT = 0X0000011A
    TC_R8_G8_B8_A8_SNORM = 0X0000021A
    TC_R8_G8_B8_A8_SINT = 0X0000031A
    TCS_R8_G8_B8_A8_SRGB = 0X0000041A
    TCS_A2_B10_G10_R10_UNORM = 0X0000001B
    TC_A2_B10_G10_R10_UINT = 0X0000011B
    D_D32_FLOAT_S8_UINT_X24 = 0X0000081C
    T_R32_FLOAT_X8_X24 = 0X0000081C
    T_X32_G8_UINT_X24 = 0X0000011C
    TC_R32_G32_UINT = 0X0000011D
    TC_R32_G32_SINT = 0X0000031D
    TC_R32_G32_FLOAT = 0X0000081E
    TC_R16_G16_B16_A16_UNORM = 0X0000001F
    TC_R16_G16_B16_A16_UINT = 0X0000011F
    TC_R16_G16_B16_A16_SNORM = 0X0000021F
    TC_R16_G16_B16_A16_SINT = 0X0000031F
    TC_R16_G16_B16_A16_FLOAT = 0X00000820
    TC_R32_G32_B32_A32_UINT = 0X00000122
    TC_R32_G32_B32_A32_SINT = 0X00000322
    TC_R32_G32_B32_A32_FLOAT = 0X00000823
    T_BC1_UNORM = 0X00000031
    T_BC1_SRGB = 0X00000431
    T_BC2_UNORM = 0X00000032
    T_BC2_SRGB = 0X00000432
    T_BC3_UNORM = 0X00000033
    T_BC3_SRGB = 0X00000433
    T_BC4_UNORM = 0X00000034
    T_BC4_SNORM = 0X00000234
    T_BC5_UNORM = 0X00000035
    T_BC5_SNORM = 0X00000235
    T_NV12_UNORM = 0X00000081


class GX2SurfaceUse(IntFlag):
    """Represents Indicates how a given surface may be used. A final TV render
    target is one that will be copied to a TV scan buffer. It needs to be
    designated to handle certain display corner cases (when a HD surface
    must be scaled down to display in NTSC/PAL)."""
    TEXTURE = 1 << 0
    COLOR_BUFFER = 1 << 1
    DEPTH_BUFFER = 1 << 2
    SCAN_BUFFER = 1 << 3
    FINAL_TV = 1 << 31
    COLOR_BUFFER_TEXTURE = TEXTURE | COLOR_BUFFER
    DEPTH_BUFFER_TEXTURE = TEXTURE | DEPTH_BUFFER
    COLOR_BUFFER_FINAL_TV = FINAL_TV | COLOR_BUFFER
    COLOR_BUFFER_TEXTURE_FINAL_TV = FINAL_TV | COLOR_BUFFER_TEXTURE


class GX2TexAnisoRatio(IntEnum):
    """Represents maximum desired anisotropic filter ratios.
    Higher ratios give better image quality, but slower performance.
    """
    RATIO_1_1 = 0
    RATIO_2_1 = 1
    RATIO_4_1 = 2
    RATIO_8_1 = 3
    RATIO_16_1 = 4


class GX2TexBorderType(IntEnum):
    """Represents type of border color to use."""
    CLEAR_BLACK = 0
    SOLID_BLACK = 1
    SOLID_WHITE = 2
    USE_REGISTER = 3


class GX2TexClamp(IntEnum):
    """Represents how to treat texture coordinates outside of the normalized coordinate texture range."""
    WRAP = 0
    MIRROR = 1
    CLAMP = 2
    MIRROR_ONCE = 3
    CLAMP_HALF_BORDER = 4
    MIRROR_ONCE_HALF_BORDER = 5
    CLAMP_BORDER = 6
    MIRROR_ONCE_BORDER = 7
    CLAMP_TO_EDGE = 8


class GX2TexMipFilterType(IntEnum):
    """Represents desired texture filter options between mip levels."""
    NO_MIP = 0
    POINT = 1
    LINEAR = 2


class GX2TexXYFilterType(IntEnum):
    """Represents desired texture filter options within a plane."""
    POINT = 0
    BILINEAR = 1


class GX2TexZFilterType(IntEnum):
    """Represents desired texture filter options between Z planes."""
    USE_XY = 0
    POINT = 1
    LINEAR = 2


class GX2TileMode(IntEnum):
    """Represents the desired tiling modes for a surface."""
    DEFAULT = 0
    LINEAR_ALIGNED = 1
    MODE1D_TILED_THIN1 = 2
    MODE1D_TILED_THICK = 3
    MODE2D_TILED_THIN1 = 4
    MODE2D_TILED_THIN2 = 5
    MODE2D_TILED_THIN4 = 6
    MODE2D_TILED_THICK = 7
    MODE2B_TILED_THIN1 = 8
    MODE2B_TILED_THIN2 = 9
    MODE2B_TILED_THIN4 = 10
    MODE2B_TILED_THICK = 11
    MODE3D_TILED_THIN1 = 12
    MODE3D_TILED_THICK = 13
    MODE3B_TILED_THIN1 = 14
    MODE3B_TILED_THICK = 15
    LINEAR_SPECIAL = 16
