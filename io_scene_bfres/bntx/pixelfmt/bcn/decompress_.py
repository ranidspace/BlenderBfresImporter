#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BC3 Compressor/Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

# decompress_.py
# A BC3/DXT5 decompressor in Python based on libtxc_dxtn.

################################################################
################################################################
from ...pixelfmt.swizzle import div_round_up
import struct
import numpy as np


def to_signed_8(v):
    if (v > 255):
        return -1

    elif (v < 0):
        return 0

    elif (v > 127):
        return v - 256

    return v


def to_unsigned_8(v):
    if (v > 127):
        return 127

    elif (v < -128):
        return 128

    elif (v < 0):
        return v + 256

    return v


def decode_rgb565(col):
    output = bytearray(4)
    B = ((col >> 0) & 0x1f) << 3
    G = ((col >> 5) & 0x3f) << 2
    R = ((col >> 11) & 0x1f) << 3

    output[0] = R | R >> 5
    output[1] = G | G >> 5
    output[2] = B | B >> 5  # the leftmost bit gets ORd to the rightmost bit?
    output[3] = 0xFF

    return bytes(output)


def c2_decode(color, c0, c1, isBC1):
    output = bytearray(4)
    if (c0 > c1 or not isBC1):
        output[0] = ((color[0][0] * 2 + color[1][0]) // 3)
        output[1] = ((color[0][1] * 2 + color[1][1]) // 3)
        output[2] = ((color[0][2] * 2 + color[1][2]) // 3)

    else:
        output[0] = ((color[0][0] + color[1][0]) // 2)
        output[1] = ((color[0][1] + color[1][1]) // 2)
        output[2] = ((color[0][2] + color[1][2]) // 2)
    output[3] = 0xFF
    color[2] = bytes(output)


def c3_decode(color, c0, c1, isBC1):
    output = bytearray(4)
    if (c0 > c1 or not isBC1):
        output[0] = ((color[0][0] + color[1][0] * 2) // 3)
        output[1] = ((color[0][1] + color[1][1] * 2) // 3)
        output[2] = ((color[0][2] + color[1][2] * 2) // 3)
        output[3] = 0xFF
        color[3] = bytes(output)
    else:
        color[3] = b'\x00\x00\x00\x00'


def exp4to8(col):
    return col | col << 4


def dxt135_imageblock(data, blksrc, isBC1):
    color = [b''] * 4
    c0 = struct.unpack_from('<H', data, blksrc)[0]
    c1 = struct.unpack_from('<H', data, blksrc + 2)[0]
    bits = struct.unpack_from('<I', data, blksrc + 4)[0]
    color[0] = decode_rgb565(c0)
    color[1] = decode_rgb565(c1)

    c2_decode(color, c0, c1, isBC1)
    c3_decode(color, c0, c1, isBC1)
    return color, bits


def dxt5_alphablock(data, blksrc):
    alpha = bytearray(8)
    alpha[0] = data[blksrc]
    alpha[1] = data[blksrc + 1]
    if (alpha[0] > alpha[1]):
        for i in range(2, 8):
            alpha[i] = (alpha[0] * (8 - i) + (alpha[1] * (i - 1))) // 7
    else:
        for i in range(2, 6):
            alpha[i] = (alpha[0] * (6 - i) + (alpha[1] * (i - 1))) // 5
        alpha[6] = 0x00
        alpha[7] = 0xFF
    return bytes(alpha)


def dxt5_alphablock_signed(data, blksrc):
    alpha = bytearray(8)
    alpha[0] = data[blksrc]
    alpha[1] = data[blksrc + 1]
    if (to_signed_8(alpha[0]) > to_signed_8(alpha[1])):
        for i in range(2, 8):
            alpha[i] = to_unsigned_8(
                (to_signed_8(alpha[0]) * (8 - i) + (to_signed_8(alpha[1]) * (i - 1))) // 7)
    else:
        for i in range(2, 6):
            alpha[i] = to_unsigned_8(
                (to_signed_8(alpha[0]) * (6 - i) + (to_signed_8(alpha[1]) * (i - 1))) // 5)
        alpha[6] = 0x80
        alpha[7] = 0x7f
    return bytes(alpha)


def decomp_dxt51(data, width, height):
    output = bytearray(width * height * 4)
    h = div_round_up(height, 4)
    w = div_round_up(width, 4)
    th = height if (height < 4) else 4
    tw = width if (width < 4) else 4

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 8
            shift = 0
            rgba, bits = dxt135_imageblock(data, blksrc, 1)

            for ty in range(th):
                for tx in range(tw):
                    pos = ((y * 4 + ty) * width + (x * 4 + tx)) * 4
                    idx = (bits >> shift & 3)

                    shift += 2
                    output[pos:pos + 4] = rgba[idx]

    return bytes(output)


def decomp_dxt53(data, width, height):
    # XXX Untested code, dont know any models which use BC2 textures
    output = bytearray(width * height * 4)
    h = div_round_up(height, 4)
    w = div_round_up(width, 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 16
            rgba, bits = dxt135_imageblock(data, blksrc + 8, 0)

            shift = 0
            for ty in range(4):
                for tx in range(4):
                    anibble = (data[blksrc + (ty * 4 + tx) // 2]
                               >> (4 * (tx & 1))) & 0xf

                    pos = ((y * 4 + ty) * width + (x * 4 + tx)) * 4
                    idx = (bits >> shift & 3)

                    shift += 2
                    pixel = rgba[idx]
                    pixel[3] = exp4to8(anibble)

                    output[pos:pos + 4] = pixel

    return bytes(output)


def decomp_dxt55(data, width, height):
    # XXX Untested code, dont know any models which use BC3 textures
    output = bytearray(width * height * 4)
    h = div_round_up(height, 4)
    w = div_round_up(width, 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 16
            tile, bits = dxt135_imageblock(data, blksrc + 8, 0)
            A = dxt5_alphablock(data, blksrc)
            AlphaCh = int.from_bytes(data[blksrc + 2:blksrc + 8], 'little')

            IdxShift = 0
            for ty in range(4):
                for tx in range(4):
                    ooffs = ((y * 4 + ty) * width + (x * 4 + tx)) * 4
                    idx = (bits >> IdxShift & 3)

                    IdxShift += 2
                    output[ooffs:ooffs + 3] = tile[idx][0:3]
                    output[ooffs + 3] = A[(AlphaCh >> (ty * 12 + tx * 3)) & 7]

    return bytes(output)


def decomp_bc4(data, width, height, snorm):
    output = bytearray(width * height)
    h = div_round_up(height, 4)
    w = div_round_up(width, 4)
    th = height if (height < 4) else 4
    tw = width if (width < 4) else 4

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 8
            if (snorm):
                R = dxt5_alphablock_signed(data, blksrc)

            else:
                R = dxt5_alphablock(data, blksrc)

            RedCh = int.from_bytes(data[blksrc + 2:blksrc + 8], 'little')

            tw = min(width - x * 4, 4)
            th = min(height - y * 4, 4)
            for ty in range(th):
                for tx in range(tw):
                    shift = ty * 12 + tx * 3  # the position times three
                    ooffs = ((y * 4 + ty) * width + (x * 4 + tx))
                    if (snorm):
                        output[ooffs +
                               0] = to_signed_8(R[(RedCh >> shift) & 7]) + 0x80
                    else:
                        output[ooffs + 0] = R[(RedCh >> shift) & 7]

    return bytes(output)


def decomp_bc5(data, width, height, snorm):
    output = bytearray(2 * width * height)
    np.empty([2, width * height], dtype='uint8')

    h = div_round_up(height, 4)
    w = div_round_up(width, 4)
    th = height if (height < 4) else 4
    tw = width if (width < 4) else 4

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 16

            if (snorm):
                R = dxt5_alphablock_signed(data, blksrc)
                G = dxt5_alphablock_signed(data, blksrc + 8)
            else:
                R = dxt5_alphablock(data, blksrc)
                G = dxt5_alphablock(data, blksrc + 8)

            RedCh = int.from_bytes(data[blksrc + 2:blksrc + 8], 'little')
            GreenCh = int.from_bytes(data[blksrc + 10:blksrc + 16], 'little')

            tw = min(width - x * 4, 4)
            th = min(height - y * 4, 4)
            for ty in range(th):
                for tx in range(tw):
                    shift = ty * 12 + tx * 3  # the position times three
                    ooffs = ((y * 4 + ty) * width + (x * 4 + tx)) * 2
                    if (snorm):
                        output[ooffs] = to_signed_8(
                            R[(RedCh >> shift) & 7]) + 0x80
                        output[ooffs + 1] = to_signed_8(
                            G[(GreenCh >> shift) & 7]) + 0x80
                    else:
                        output[ooffs] = R[(RedCh >> shift) & 7]
                        output[ooffs + 1] = G[(GreenCh >> shift) & 7]

    return bytes(output)
