# BC3 Compressor/Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

# decompress_.py
# A BC3/DXT5 decompressor in Python based on libtxc_dxtn.

################################################################
################################################################
import math
import struct

import numpy as np


def to_signed_8(v):
    if v > 255:
        return -1

    if v < 0:
        return 0

    if v > 127:
        return v - 256

    return v


def to_unsigned_8(v):
    if v > 127:
        return 127

    if v < -128:
        return 128

    if v < 0:
        return v + 256

    return v


def decode_rgb565(col):
    output = bytearray(4)
    b = ((col >> 0) & 0x1F) << 3
    g = ((col >> 5) & 0x3F) << 2
    r = ((col >> 11) & 0x1F) << 3

    output[0] = r | r >> 5
    output[1] = g | g >> 5
    output[2] = b | b >> 5  # the leftmost bit gets ORd to the rightmost bit?
    output[3] = 0xFF

    return bytes(output)


def c2_decode(color, c0, c1, is_bc1):
    output = bytearray(4)
    if c0 > c1 or not is_bc1:
        output[0] = (color[0][0] * 2 + color[1][0]) // 3
        output[1] = (color[0][1] * 2 + color[1][1]) // 3
        output[2] = (color[0][2] * 2 + color[1][2]) // 3

    else:
        output[0] = (color[0][0] + color[1][0]) // 2
        output[1] = (color[0][1] + color[1][1]) // 2
        output[2] = (color[0][2] + color[1][2]) // 2
    output[3] = 0xFF
    color[2] = bytes(output)


def c3_decode(color, c0, c1, is_bc1):
    output = bytearray(4)
    if c0 > c1 or not is_bc1:
        output[0] = (color[0][0] + color[1][0] * 2) // 3
        output[1] = (color[0][1] + color[1][1] * 2) // 3
        output[2] = (color[0][2] + color[1][2] * 2) // 3
        output[3] = 0xFF
        color[3] = bytes(output)
    else:
        color[3] = b"\x00\x00\x00\x00"


def exp4to8(col):
    return col | col << 4


def dxt135_imageblock(data, blksrc, is_bc1):
    color = [b""] * 4
    c0 = struct.unpack_from("<H", data, blksrc)[0]
    c1 = struct.unpack_from("<H", data, blksrc + 2)[0]
    bits = struct.unpack_from("<I", data, blksrc + 4)[0]
    color[0] = decode_rgb565(c0)
    color[1] = decode_rgb565(c1)

    c2_decode(color, c0, c1, is_bc1)
    c3_decode(color, c0, c1, is_bc1)
    return color, bits


def dxt5_alphablock(data, blksrc):
    alpha = bytearray(8)
    alpha[0] = data[blksrc]
    alpha[1] = data[blksrc + 1]
    if alpha[0] > alpha[1]:
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
    alpha_0 = to_signed_8(alpha[0])
    alpha_1 = to_signed_8(alpha[1])
    if alpha_0 > alpha_1:
        for i in range(2, 8):
            alpha[i] = to_unsigned_8((alpha_0 * (8 - i) + alpha_1 * (i - 1)) // 7)
    else:
        for i in range(2, 6):
            alpha[i] = to_unsigned_8((alpha_0 * (6 - i) + alpha_1 * (i - 1)) // 5)
        alpha[6] = 0x80
        alpha[7] = 0x7F
    return bytes(alpha)


def decomp_dxt51(data, width, height):
    output = bytearray(width * height * 4)
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 8
            shift = 0
            rgba, bits = dxt135_imageblock(data, blksrc, 1)

            tw = min(width - x * 4, 4)
            th = min(height - y * 4, 4)
            for ty in range(th):
                for tx in range(tw):
                    pos = ((y * 4 + ty) * width + (x * 4 + tx)) * 4
                    idx = bits >> shift & 3

                    shift += 2
                    output[pos : pos + 4] = rgba[idx]

    return bytes(output)


def decomp_dxt53(data, width, height):
    # XXX Untested code, dont know any models which use BC2 textures
    output = bytearray(width * height * 4)
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 16
            rgba, bits = dxt135_imageblock(data, blksrc + 8, 0)

            shift = 0
            for ty in range(4):
                for tx in range(4):
                    anibble = (data[blksrc + (ty * 4 + tx) // 2] >> (4 * (tx & 1))) & 0xF

                    pos = ((y * 4 + ty) * width + (x * 4 + tx)) * 4
                    idx = bits >> shift & 3

                    shift += 2
                    pixel = rgba[idx]
                    pixel[3] = exp4to8(anibble)

                    output[pos : pos + 4] = pixel

    return bytes(output)


def decomp_dxt55(data, width, height):
    # XXX Untested code, dont know any models which use BC3 textures
    output = bytearray(width * height * 4)
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 16
            tile, bits = dxt135_imageblock(data, blksrc + 8, 0)
            alpha_block = dxt5_alphablock(data, blksrc)
            alpha_select = int.from_bytes(data[blksrc + 2 : blksrc + 8], "little")

            idx_shift = 0
            for ty in range(4):
                for tx in range(4):
                    ooffs = ((y * 4 + ty) * width + (x * 4 + tx)) * 4
                    idx = bits >> idx_shift & 3

                    idx_shift += 2
                    output[ooffs : ooffs + 3] = tile[idx][0:3]
                    output[ooffs + 3] = alpha_block[(alpha_select >> (ty * 12 + tx * 3)) & 7]

    return bytes(output)


def decomp_bc4(data, width, height, snorm):
    output = bytearray(width * height)
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 8
            if snorm:
                alpha_block = dxt5_alphablock_signed(data, blksrc)

            else:
                alpha_block = dxt5_alphablock(data, blksrc)

            alpha_select = int.from_bytes(data[blksrc + 2 : blksrc + 8], "little")

            tw = min(width - x * 4, 4)
            th = min(height - y * 4, 4)
            for ty in range(th):
                for tx in range(tw):
                    shift = ty * 12 + tx * 3  # the position times three
                    ooffs = (y * 4 + ty) * width + (x * 4 + tx)
                    if snorm:
                        output[ooffs] = to_signed_8(alpha_block[(alpha_select >> shift) & 7]) + 0x80
                    else:
                        output[ooffs] = alpha_block[(alpha_select >> shift) & 7]

    return bytes(output)


def decomp_bc5(data, width, height, snorm):
    output = bytearray(2 * width * height)
    np.empty([2, width * height], dtype="uint8")

    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    for y in range(h):
        for x in range(w):
            blksrc = (y * w + x) * 16

            if snorm:
                red_block = dxt5_alphablock_signed(data, blksrc)
                grn_block = dxt5_alphablock_signed(data, blksrc + 8)
            else:
                red_block = dxt5_alphablock(data, blksrc)
                grn_block = dxt5_alphablock(data, blksrc + 8)

            red_select = int.from_bytes(data[blksrc + 2 : blksrc + 8], "little")
            grn_select = int.from_bytes(data[blksrc + 10 : blksrc + 16], "little")

            tw = min(width - x * 4, 4)
            th = min(height - y * 4, 4)
            for ty in range(th):
                for tx in range(tw):
                    shift = ty * 12 + tx * 3  # the position times three
                    ooffs = ((y * 4 + ty) * width + (x * 4 + tx)) * 2
                    if snorm:
                        output[ooffs] = to_signed_8(red_block[(red_select >> shift) & 7]) + 0x80
                        output[ooffs + 1] = to_signed_8(grn_block[(grn_select >> shift) & 7]) + 0x80
                    else:
                        output[ooffs] = red_block[(red_select >> shift) & 7]
                        output[ooffs + 1] = grn_block[(grn_select >> shift) & 7]

    return bytes(output)
