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
import numpy.typing as npt

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
        return decompress_.decomp_bc1(data, width, height)

    @staticmethod
    def decodepixels(data: npt.NDArray[np.uint8]):
        return data / 255.0


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
        return decompress_.decomp_bc2(data, width, height)

    @staticmethod
    def decodepixels(data: npt.NDArray[np.uint8]):
        return data / 255.0


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
        return decompress_.decomp_bc3(data, width, height)

    @staticmethod
    def decodepixels(data: npt.NDArray[np.uint8]):
        return data


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

    # NOTE: Blender images seem to need all 4 channels
    @staticmethod
    def decodepixels(data: npt.NDArray[np.float32]):
        data = data[..., np.newaxis].repeat(3, axis=-1)
        return np.dstack((data, np.ones(data.shape[0:2])[..., np.newaxis]))


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

    # NOTE: Blender images seem to need all 4 channels
    @staticmethod
    def decodepixels(data: npt.NDArray[np.float32]):
        data = np.dstack(
            (
                data,
                np.real(np.sqrt(abs(1 - data[..., 0] ** 2 - data[..., 1])))[..., np.newaxis],
                np.ones(data.shape[0:2]),
            ),
        )

        return data + 1.0 / 2.0
