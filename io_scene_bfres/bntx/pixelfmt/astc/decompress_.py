# Adapted from https://github.com/ARM-software/astc-encoder
# Under an Apache-2.0 License
from enum import IntEnum
from dataclasses import dataclass

class QuantMethod(IntEnum):
    QUANT_2 = 0
    QUANT_3 = 1
    QUANT_4 = 2
    QUANT_5 = 3
    QUANT_6 = 4
    QUANT_8 = 5
    QUANT_10 = 6
    QUANT_12 = 7
    QUANT_16 = 8
    QUANT_20 = 9
    QUANT_24 = 10
    QUANT_32 = 11
    QUANT_40 = 12
    QUANT_48 = 13
    QUANT_64 = 14
    QUANT_80 = 15
    QUANT_96 = 16
    QUANT_128 = 17
    QUANT_160 = 18
    QUANT_192 = 19
    QUANT_256 = 20


@dataclass()
class BlockMode:
    x_weights: int
    y_weights: int
    is_dual_plane: bool
    quant_mode: int
    weight_bits: int

def get_ise_sequence_bitcount():

def decode_block_mode_2d(block_mode) -> BlockMode | None:
    base_quant_mode = (block_mode >> 4) & 1
    h = (block_mode >> 9) & 1
    d = (block_mode >> 10) & 1
    a = (block_mode >> 5) & 0x3

    x_weights = 0
    y_weights = 0

    if (block_mode & 3) != 0:
        base_quant_mode |= (block_mode & 3) << 1
        b = (block_mode >> 7) & 3
        match (block_mode >> 2) & 3:
            case 0:
                x_weights = b + 4
                y_weights = a + 2
            case 1:
                x_weights = b + 8
                y_weights = a + 2
            case 2:
                x_weights = a + 2
                y_weights = b + 8
            case 3:
                b &= 1
                if block_mode & 0x100:
                    x_weights = b + 2
                    y_weights = a + 2
                else:
                    x_weights = a + 2
                    y_weights = b + 6
    else:
        base_quant_mode |= ((block_mode >> 2) & 3) << 1
        if ((block_mode >> 2) & 3) == 0:
            return None

        b = (block_mode >> 9) & 3
        match ((block_mode >> 7) & 3):
            case 0:
                x_weights = 12
                y_weights = a + 2
            case 1:
                x_weights = a + 2
                y_weights = 12
            case 2:
                x_weights = a + 6
                y_weights = b + 6
                d = 0
                h = 0
            case 3:
                match (block_mode >> 5) & 3:
                    case 0:
                        x_weights = 6
                        y_weights = 10
                    case 1:
                        x_weights = 10
                        y_weights = 6
                    case 2 | 3:
                        return None

    weight_count = x_weights * y_weights * (d + 1)
    quant_mode = (base_quant_mode - 2) + 6 * h
    is_dual_plane = d != 0


    return BlockMode(x_weights, y_weights, is_dual_plane, quant_mode, )

def astc_decompress_image(context, data):
    pass
