from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from astc_encoder import (
    ASTCConfig,
    ASTCContext,
    ASTCImage,
    ASTCProfile,
    ASTCSwizzle,
    ASTCType,
)

from ..base import TextureFormat

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...brti import BRTI


def decomp_astc(data: bytes, width: int, height: int, config: ASTCConfig):
    context = ASTCContext(config)
    swizzle = ASTCSwizzle.from_str("RGBA")

    img_dec = ASTCImage(ASTCType.U8, width, height)
    output = context.decompress(data, img_dec, swizzle)
    return output.data


class Astc5x5(TextureFormat):
    _FORMAT_ID = 0x2F

    @staticmethod
    def decompress(tex: BRTI):
        data = tex.mip_data
        width = tex.width
        height = tex.height

        config = ASTCConfig(ASTCProfile.LDR_SRGB, 5, 5)

        return decomp_astc(data, width, height, config)


class Astc6x6(TextureFormat):
    _FORMAT_ID = 0x31

    @staticmethod
    def decompress(tex: BRTI):
        data = tex.mip_data
        width = tex.width
        height = tex.height

        config = ASTCConfig(ASTCProfile.LDR_SRGB, 6, 6)

        return decomp_astc(data, width, height, config)

    # "ASTC4x4": {"id": 0x2D, "bpp": 16},
    # "ASTC5x4": {"id": 0x2E, "bpp": 16},
    # "ASTC6x5": {"id": 0x30, "bpp": 16},
    # "ASTC8x5": {"id": 0x32, "bpp": 16},
    # "ASTC8x6": {"id": 0x33, "bpp": 16},
    # "ASTC8x8": {"id": 0x34, "bpp": 16},
    # "ASTC10x5": {"id": 0x35, "bpp": 16},
    # "ASTC10x6": {"id": 0x36, "bpp": 16},
    # "ASTC10x8": {"id": 0x37, "bpp": 16},
    # "ASTC10x10": {"id": 0x38, "bpp": 16},
    # "ASTC12x10": {"id": 0x39, "bpp": 16},
    # "ASTC12x12": {"id": 0x3A, "bpp": 16},
