# This file is a modified part of botwtools.
#
# botwtools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# botwtools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with botwtools.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import logging
from typing import ClassVar, TYPE_CHECKING

import numpy as np

from .formatinfo import bpps

if TYPE_CHECKING:
    from ..brti import BRTI
log = logging.getLogger(__name__)


types = {  # name => id, bytes per pixel
    "R5G6B5": {"id": 0x07, "bpp": 2},
    "R8": {"id": 0x02, "bpp": 1},
    "R8G8": {"id": 0x09, "bpp": 2},
    "R16": {"id": 0x0A, "bpp": 2},
    "R8G8B8A8": {"id": 0x0B, "bpp": 4},
    "R11G11B10": {"id": 0x0F, "bpp": 4},
    "R32": {"id": 0x14, "bpp": 4},
    "BC1": {"id": 0x1A, "bpp": 8},
    "BC2": {"id": 0x1B, "bpp": 16},
    "BC3": {"id": 0x1C, "bpp": 16},
    "BC4": {"id": 0x1D, "bpp": 8},
    "BC5": {"id": 0x1E, "bpp": 16},
    "BC6": {"id": 0x1F, "bpp": 8},  # XXX verify bpp
    "BC7": {"id": 0x20, "bpp": 8},
    "ASTC4x4": {"id": 0x2D, "bpp": 16},
    "ASTC5x4": {"id": 0x2E, "bpp": 16},
    "ASTC5x5": {"id": 0x2F, "bpp": 16},
    "ASTC6x5": {"id": 0x30, "bpp": 16},
    "ASTC6x6": {"id": 0x31, "bpp": 16},
    "ASTC8x5": {"id": 0x32, "bpp": 16},
    "ASTC8x6": {"id": 0x33, "bpp": 16},
    "ASTC8x8": {"id": 0x34, "bpp": 16},
    "ASTC10x5": {"id": 0x35, "bpp": 16},
    "ASTC10x6": {"id": 0x36, "bpp": 16},
    "ASTC10x8": {"id": 0x37, "bpp": 16},
    "ASTC10x10": {"id": 0x38, "bpp": 16},
    "ASTC12x10": {"id": 0x39, "bpp": 16},
    "ASTC12x12": {"id": 0x3A, "bpp": 16},
}


class TextureFormat:
    fmts: ClassVar[dict[int, type[TextureFormat]]] = {}
    _FORMAT_ID = -1

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.fmts[cls._FORMAT_ID] = cls

    @classmethod
    def register(cls, format_id: int):
        def decorator(fmt: type[TextureFormat]):
            cls.fmts[format_id] = fmt

    @classmethod
    def get(cls, format_id):
        if format_id not in cls.fmts:
            msg = f"Unsupported texture format {hex(format_id)}"
            raise TypeError(msg)
        return cls.fmts[format_id]

    @staticmethod
    def decompress(tex: BRTI):
        bpp = bpps[tex.bpp]
        data = tex.mip_data
        pixels = bytes(tex.mip_data)
        log.debug(
            "Texture: %d bytes/pixel, %dx%d = %d, len = %d",
            bpp,
            tex.width,
            tex.height,
            tex.width * tex.height * bpp,
            len(data),
        )
        return pixels

    @staticmethod
    def decodepixels(data):
        return np.frombuffer(data, dtype="B") / 255.0

    def __str__(self):
        return f"<TextureFormat '{type(self).__name__}' at {id(self)}>"
