# This file is a modified file from
# https://github.com/aboood40091/BNTX-Editor/
# Which is licensed under GPL-3

import math
import struct
import logging
log = logging.getLogger(__name__)


def div_round_up(n, d):
    return (n + d - 1) // d


def round_up(x, y):
    return ((x - 1) | (y - 1)) + 1


def pow2_round_up(x):
    x -= 1
    x |= x >> 1
    x |= x >> 2
    x |= x >> 4
    x |= x >> 8
    x |= x >> 16

    return x + 1


def deswizzle(width, height, blk_width, blk_height, bpp, tile_mode, blk_height_log2, data):
    '''Function which returns deswizzled image data'''
    # Modified from https://github.com/aboood40091/BNTX-Editor/ which is under a GPL-3.0 License
    block_height = 1 << blk_height_log2

    width = div_round_up(width, blk_width)
    height = div_round_up(height, blk_height)

    if (tile_mode == 1):
        pitch = width * bpp

        # If wii u support is added this depends on if the header of the texture is "NX" or not
        pitch = round_up(pitch, 32)

        surf_size = pitch * height

    else:
        pitch = round_up(width * bpp, 64)
        surf_size = pitch * round_up(height, block_height * 8)

    result = bytearray(surf_size)

    for y in range(height):
        for x in range(width):
            if (tile_mode == 1):
                pos = y * pitch + x * bpp

            else:
                pos = __get_addr_block_linear(
                    x, y, width, bpp, 0, block_height)

            pos_ = (y * width + x) * bpp

            if (pos + bpp <= surf_size):
                result[pos_:pos_ + bpp] = data[pos:pos + bpp]

    return bytes(result)


def __get_addr_block_linear(x, y, image_width, bytes_per_pixel, base_address, block_height):
    image_width_in_gobs = div_round_up(image_width * bytes_per_pixel, 64)
    gob_address = (base_address
                   + (y // (8 * block_height)) * 512 *
                   block_height * image_width_in_gobs
                   + (x * bytes_per_pixel // 64) * 512 * block_height
                   + (y % (8 * block_height) // 8) * 512)

    x *= bytes_per_pixel

    addr = (gob_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
            + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return addr
