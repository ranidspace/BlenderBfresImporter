# DXT1/3/5 Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

################################################################
################################################################

# This file has been edited
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ..base import TextureFormat
from . import decompress_

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...brti import BRTI


class BC1(TextureFormat):
    _FORMAT_ID = 0x1A

    @staticmethod
    def decompress(tex: BRTI):
        data = tex.mip_data
        width = tex.width
        height = tex.height

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
        if len(data) < csize:
            log.warning("Compressed data is incomplete")
            return b""

        data = data[:csize]
        return decompress_.decomp_dxt51(data, width, height)


class BC2(TextureFormat):
    _FORMAT_ID = 0x1B
    depth = 8

    @staticmethod
    def decompress(tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
        if len(data) < csize:
            log.warning("Compressed data is incomplete")
            return b""

        data = data[:csize]
        return decompress_.decomp_dxt53(data, width, height)


class BC3(TextureFormat):
    _FORMAT_ID = 0x1C
    depth = 8

    @staticmethod
    def decompress(tex: BRTI):
        data = tex.mip_data
        width = tex.width
        height = tex.height

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
        if len(data) < csize:
            log.warning("Compressed data is incomplete")
            return b""

        data = data[:csize]
        return decompress_.decomp_dxt55(data, width, height)


class BC4(TextureFormat):
    _FORMAT_ID = 0x1D
    depth = 8

    @staticmethod
    def decompress(tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        snorm = 0 if tex.fmt_dtype == 1 else 1

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
        if len(data) < csize:
            log.warning("Compressed data is incomplete")
            return b""

        data = data[:csize]
        return decompress_.decomp_bc4(data, width, height, snorm)

    @staticmethod
    def decodepixels(data):
        rgba = np.empty(len(data) * 4)
        rgba[0::4] = rgba[1::4] = rgba[2::4] = np.frombuffer(data, dtype="B") / 255
        rgba[3::4] = 1
        return rgba


class BC5(TextureFormat):
    _FORMAT_ID = 0x1E
    depth = 8

    @staticmethod
    def decompress(tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        snorm = 0 if tex.fmt_dtype == 1 else 1

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
        if len(data) < csize:
            log.warning("Compressed data is incomplete")
            return b""

        data = data[:csize]
        return decompress_.decomp_bc5(data, width, height, snorm)

    @staticmethod
    def decodepixels(data):
        r = np.frombuffer(data[0::2], dtype=np.uint8).astype(np.float32) / 255
        g = np.frombuffer(data[1::2], dtype=np.uint8).astype(np.float32) / 255
        x = r * 2 - 1
        y = g * 2 - 1
        z = abs(1 - x**2 - y**2) ** 0.5
        rgba = np.empty(len(data) * 2, dtype=np.float32)
        rgba[0::4] = r
        rgba[1::4] = g
        rgba[2::4] = np.real((z + 1) * 0.5)
        rgba[3::4] = 1
        return rgba
