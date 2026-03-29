from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from texture2ddecoder import decode_astc

from ..base import TextureFormat
from ..formatinfo import astc_formats

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...brti import BRTI


class Astc(TextureFormat):
    _FORMAT_ID = astc_formats

    @staticmethod
    def decompress(tex: BRTI):
        return decode_astc(tex.mip_data, tex.width, tex.height, tex.blk_width, tex.blk_height)

    @staticmethod
    def decodepixels(data):
        buffer = np.frombuffer(data, dtype="B").reshape((-1, 4)) / 255.0
        buffer[:, [0, 2]] = buffer[:, [2, 0]]
        return buffer

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
