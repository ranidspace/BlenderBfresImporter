#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BNTX Editor
# Version 0.3
# Copyright © 2018 AboodXD

# This file is part of BNTX Editor.

# BNTX Editor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BNTX Editor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

version = "0.3"

formats = {
    0x0101: "R4_G4_UNORM",
    0x0201: "R8_UNORM",
    0x0301: "R4_G4_B4_A4_UNORM",
    0x0401: "A4_B4_G4_R4_UNORM",
    0x0501: "R5_G5_B5_A1_UNORM",
    0x0601: "A1_B5_G5_R5_UNORM",
    0x0701: "R5_G6_B5_UNORM",
    0x0801: "B5_G6_R5_UNORM",
    0x0901: "R8_G8_UNORM",
    0x0B01: "R8_G8_B8_A8_UNORM",
    0x0B06: "R8_G8_B8_A8_SRGB",
    0x0C01: "B8_G8_R8_A8_UNORM",
    0x0C06: "B8_G8_R8_A8_SRGB",
    0x0E01: "R10_G10_B10_A2_UNORM",
    0x1A01: "BC1_UNORM",
    0x1A06: "BC1_SRGB",
    0x1B01: "BC2_UNORM",
    0x1B06: "BC2_SRGB",
    0x1C01: "BC3_UNORM",
    0x1C06: "BC3_SRGB",
    0x1D01: "BC4_UNORM",
    0x1D02: "BC4_SNORM",
    0x1E01: "BC5_UNORM",
    0x1E02: "BC5_SNORM",
    0x1F05: "BC6_FLOAT",
    0x1F0A: "BC6_UFLOAT",
    0x2001: "BC7_UNORM",
    0x2006: "BC7_SRGB",
    0x2D01: "ASTC_4x4_UNORM",
    0x2D06: "ASTC_4x4_SRGB",
    0x2E01: "ASTC_5x4_UNORM",
    0x2E06: "ASTC_5x4_SRGB",
    0x2F01: "ASTC_5x5_UNORM",
    0x2F06: "ASTC_5x5_SRGB",
    0x3001: "ASTC_6x5_UNORM",
    0x3006: "ASTC_6x5_SRGB",
    0x3101: "ASTC_6x6_UNORM",
    0x3106: "ASTC_6x6_SRGB",
    0x3201: "ASTC_8x5_UNORM",
    0x3206: "ASTC_8x5_SRGB",
    0x3301: "ASTC_8x6_UNORM",
    0x3306: "ASTC_8x6_SRGB",
    0x3401: "ASTC_8x8_UNORM",
    0x3406: "ASTC_8x8_SRGB",
    0x3501: "ASTC_10x5_UNORM",
    0x3506: "ASTC_10x5_SRGB",
    0x3601: "ASTC_10x6_UNORM",
    0x3606: "ASTC_10x6_SRGB",
    0x3701: "ASTC_10x8_UNORM",
    0x3706: "ASTC_10x8_SRGB",
    0x3801: "ASTC_10x10_UNORM",
    0x3806: "ASTC_10x10_SRGB",
    0x3901: "ASTC_12x10_UNORM",
    0x3906: "ASTC_12x10_SRGB",
    0x3A01: "ASTC_12x12_UNORM",
    0x3A06: "ASTC_12x12_SRGB",
    0x3B01: "B5_G5_R5_A1_UNORM",
}

targets = [
    "PC (Gen)",
    "Switch (NX)",
]

accessflags = [
    "Read",
    "Write",
    "VertexBuffer",
    "IndexBuffer",
    "ConstantBuffer",
    "Texture",
    "UnorderedAccessBuffer",
    "ColorBuffer",
    "DepthStencil",
    "IndirectBuffer",
    "ScanBuffer",
    "QueryBuffer",
    "Descriptor",
    "ShaderCode",
    "Image",
]

dims = [
    "Undefined",
    "1D",
    "2D",
    "3D",
]

img_dims = [
    "1D",
    "2D",
    "3D",
    "Cube",
    "1D Array",
    "2D Array",
    "2D Multisample",
    "2D Multisample Array",
    "Cube Array",
]

tile_modes = {
    0: "Optimal",
    1: "Linear",
}

comp_sels = [
    "Zero",
    "One",
    "Red",
    "Green",
    "Blue",
    "Alpha",
]

bcn_formats = [
    0x1A,
    0x1B,
    0x1C,
    0x1D,
    0x1E,
    0x1F,
    0x20,
]

astc_formats = [
    0x2D,
    0x2E,
    0x2F,
    0x30,
    0x31,
    0x32,
    0x33,
    0x34,
    0x35,
    0x36,
    0x37,
    0x38,
    0x39,
    0x3A,
]

blk_dims = {  # format -> (blk_width, blk_height)
    0x1A: (4, 4),
    0x1B: (4, 4),
    0x1C: (4, 4),
    0x1D: (4, 4),
    0x1E: (4, 4),
    0x1F: (4, 4),
    0x20: (4, 4),
    0x2D: (4, 4),
    0x2E: (5, 4),
    0x2F: (5, 5),
    0x30: (6, 5),
    0x31: (6, 6),
    0x32: (8, 5),
    0x33: (8, 6),
    0x34: (8, 8),
    0x35: (10, 5),
    0x36: (10, 6),
    0x37: (10, 8),
    0x38: (10, 10),
    0x39: (12, 10),
    0x3A: (12, 12),
}

bpps = {  # format -> bytes_per_pixel
    0x01: 0x01,
    0x02: 0x01,
    0x03: 0x02,
    0x04: 0x02,
    0x05: 0x02,
    0x06: 0x02,
    0x07: 0x02,
    0x08: 0x02,
    0x09: 0x02,
    0x0B: 0x04,
    0x0C: 0x04,
    0x0E: 0x04,
    0x1A: 0x08,
    0x1B: 0x10,
    0x1C: 0x10,
    0x1D: 0x08,
    0x1E: 0x10,
    0x1F: 0x10,
    0x20: 0x10,
    0x2D: 0x10,
    0x2E: 0x10,
    0x2F: 0x10,
    0x30: 0x10,
    0x31: 0x10,
    0x32: 0x10,
    0x33: 0x10,
    0x34: 0x10,
    0x35: 0x10,
    0x36: 0x10,
    0x37: 0x10,
    0x38: 0x10,
    0x39: 0x10,
    0x3A: 0x10,
    0x3B: 0x02,
}


filedata = bytearray()
tex_sizes = []
