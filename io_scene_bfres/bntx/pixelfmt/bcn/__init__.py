#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DXT1/3/5 Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

################################################################
################################################################

# This file has been edited

import numpy as np
from . import decompress_
from .. import TextureFormat
from . dx10 import BC7


class BC1(TextureFormat):
    id = 0x1a
    bytes_per_pixel = 4
    depth = 8

    def decompress(self, tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        if (not isinstance(data, bytes)):
            try:
                data = bytes(data)

            except:
                print("Couldn't decompress data")
                return b''

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
        if (len(data) < csize):
            print("Compressed data is incomplete")
            return b''

        data = data[:csize]
        return decompress_.decomp_dxt51(data, width, height)


class BC2(TextureFormat):
    id = 0x1b
    bytes_per_pixel = 4
    depth = 8

    def decompress(self, tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        if (not isinstance(data, bytes)):
            try:
                data = bytes(data)

            except:
                print("Couldn't decompress data")
                return b''

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
        if (len(data) < csize):
            print("Compressed data is incomplete")
            return b''

        data = data[:csize]
        return decompress_.decomp_dxt53(data, width, height)


class BC3(TextureFormat):
    id = 0x1c
    bytes_per_pixel = 4
    depth = 8

    def decompress(self, tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        if (not isinstance(data, bytes)):
            try:
                data = bytes(data)

            except:
                print("Couldn't decompress data")
                return b''

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
        if (len(data) < csize):
            print("Compressed data is incomplete")
            return b''

        data = data[:csize]
        return decompress_.decomp_dxt55(data, width, height)


class BC4(TextureFormat):
    id = 0x1d
    bytes_per_pixel = 4
    depth = 8

    def decompress(self, tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        snorm = 0 if tex.fmt_dtype == 1 else 1
        if (not isinstance(data, bytes)):
            try:
                data = bytes(data)

            except:
                print("Couldn't decompress data")
                return b''

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
        if (len(data) < csize):
            print("Compressed data is incomplete")
            return b''

        data = data[:csize]
        return decompress_.decomp_bc4(data, width, height, snorm)

    @staticmethod
    def decodepixels(data):
        rgba = np.empty(len(data) * 4)
        rgba[0::4] = rgba[1::4] = rgba[2::4] = np.frombuffer(data, dtype='B') / 255
        rgba[3::4] = 1
        return rgba


class BC5(TextureFormat):
    id = 0x1e
    bytes_per_pixel = 4
    depth = 8

    def decompress(self, tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        snorm = 0 if tex.fmt_dtype == 1 else 1
        if (not isinstance(data, bytes)):
            try:
                data = bytes(data)

            except:
                print("Couldn't decompress data")
                return b''

        csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
        if (len(data) < csize):
            print("Compressed data is incomplete")
            return b''

        data = data[:csize]
        return decompress_.decomp_bc5(data, width, height, snorm)

    @staticmethod
    def decodepixels(data):
        r = np.frombuffer(data[0::2], dtype=np.uint8).astype(np.float32) / 255
        g = np.frombuffer(data[1::2], dtype=np.uint8).astype(np.float32) / 255
        x = r * 2 - 1
        y = g * 2 - 1
        z = abs(1 - x**2 - y**2)**0.5
        rgba = np.empty(len(data) * 2, dtype=np.float32)
        rgba[0::4] = r
        rgba[1::4] = g
        rgba[2::4] = np.real((z + 1) * 0.5)
        rgba[3::4] = 1
        return rgba
