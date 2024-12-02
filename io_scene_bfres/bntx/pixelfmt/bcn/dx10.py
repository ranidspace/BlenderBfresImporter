from .. import TextureFormat
from dataclasses import dataclass
from typing import overload
import numpy as np

# https://github.com/KFreon/CSharpImageLibrary
# This part is from DX10_Helpers

partitiontable = [
    # Table.P2
    # (each row is one 4x4 block)
    # BC6H/BC7 Partition Set for 2 Subsets
    [
        0xcccc, 0x8888, 0xeeee, 0xecc8, 0xc880, 0xfeec, 0xfec8, 0xec80, 0xc800,
        0xffec, 0xfe80, 0xe800, 0xffe8, 0xff00, 0xfff0, 0xf000, 0xf710, 0x008e,
        0x7100, 0x08ce, 0x008c, 0x7310, 0x3100, 0x8cce, 0x088c, 0x3110, 0x6666,
        0x366c, 0x17e8, 0x0ff0, 0x718e, 0x399c, 0xaaaa, 0xf0f0, 0x5a5a, 0x33cc,
        0x3c3c, 0x55aa, 0x9696, 0xa55a, 0x73ce, 0x13c8, 0x324c, 0x3bdc, 0x6996,
        0xc33c, 0x9966, 0x0660, 0x0272, 0x04e4, 0x4e40, 0x2720, 0xc936, 0x936c,
        0x39c6, 0x639c, 0x9336, 0x9cc6, 0x817e, 0xe718, 0xccf0, 0x0fcc, 0x7744,
        0xee22
    ],
    # Table.P3
    # BC7 Partition Set for 3 Subsets
    [
        0xaa685050, 0x6a5a5040, 0x5a5a4200, 0x5450a0a8, 0xa5a50000, 0xa0a05050,
        0x5555a0a0, 0x5a5a5050, 0xaa550000, 0xaa555500, 0xaaaa5500, 0x90909090,
        0x94949494, 0xa4a4a4a4, 0xa9a59450, 0x2a0a4250, 0xa5945040, 0x0a425054,
        0xa5a5a500, 0x55a0a0a0, 0xa8a85454, 0x6a6a4040, 0xa4a45000, 0x1a1a0500,
        0x0050a4a4, 0xaaa59090, 0x14696914, 0x69691400, 0xa08585a0, 0xaa821414,
        0x50a4a450, 0x6a5a0200, 0xa9a58000, 0x5090a0a8, 0xa8a09050, 0x24242424,
        0x00aa5500, 0x24924924, 0x24499224, 0x50a50a50, 0x500aa550, 0xaaaa4444,
        0x66660000, 0xa5a0a5a0, 0x50a050a0, 0x69286928, 0x44aaaa44, 0x66666600,
        0xaa444444, 0x54a854a8, 0x95809580, 0x96969600, 0xa85454a8, 0x80959580,
        0xaa141414, 0x96960000, 0xaaaa1414, 0xa05050a0, 0xa0a5a5a0, 0x96000000,
        0x40804080, 0xa9a8a9a8, 0xaaaaaa44, 0x2a4a5254
    ]
]

anchor_table = [
    # Table.A2
    [
        15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
        15, 15, 15, 2, 8, 2, 2, 8, 8, 15, 2, 8, 2, 2, 8, 8, 2,
        2, 15, 15, 6, 8, 2, 8, 15, 15, 2, 8, 2, 2, 2, 15, 15, 6,
        6, 2, 6, 8, 15, 15, 2, 2, 15, 15, 15, 15, 15, 2, 2, 15,

    ],
    # Table.A3a
    [
        3, 3, 15, 15, 8, 3, 15, 15, 8, 8, 6, 6, 6, 5, 3, 3, 3,
        3, 8, 15, 3, 3, 6, 10, 5, 8, 8, 6, 8, 5, 15, 15, 8, 15,
        3, 5, 6, 10, 8, 15, 15, 3, 15, 5, 15, 15, 15, 15, 3, 15,
        5, 5, 5, 8, 5, 10, 5, 10, 8, 13, 15, 12, 3, 3,
    ],
    # Table.A3b
    [
        15, 8, 8, 3, 15, 15, 3, 8, 15, 15, 15, 15, 15, 15, 15, 8,
        15, 8, 15, 3, 15, 8, 15, 8, 3, 15, 6, 10, 15, 15, 10, 8,
        15, 3, 15, 10, 10, 8, 9, 10, 6, 15, 8, 15, 3, 6, 6, 8, 15,
        3, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 3, 15, 15, 8,
    ]

]


def get_subset(num_subsets: int, partition: int, offs: int):
    if num_subsets == 2:
        return 1 & (partitiontable[0][partition] >> offs)
    if num_subsets == 3:
        return 3 & (partitiontable[1][partition] >> (2 * offs))
    return 0


aweights2 = [0, 21, 43, 64]
aweights3 = [0, 9, 18, 27, 37, 46, 55, 64]
aweights4 = [0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64]


def get_weights(n: int):
    if (n == 2):
        return aweights2
    if (n == 3):
        return aweights3
    return aweights4


def getbit(source, srcstart, start) -> int:
    uidx = start[0] >> 3
    ret = (source[srcstart + uidx] >> (start[0] - (uidx << 3))) & 0x01
    start[0] += 1

    return ret


def getbits(source, srcstart, start, length) -> int:
    if (length == 0):
        return 0
    uidx = start[0] >> 3
    ubase = start[0] - (uidx << 3)
    ret = 0

    if (ubase + length > 8):
        firstidxbits = 8 - ubase
        nextidxbits = length - firstidxbits
        ret = (
            (source[srcstart + uidx] >> ubase)
            | ((source[srcstart + uidx + 1]
                & ((1 << nextidxbits) - 1)) << firstidxbits))
    else:
        ret = (source[srcstart + uidx] >> ubase) & ((1 << length) - 1)

    start[0] += length
    return ret


class BC6(TextureFormat):
    @dataclass
    class Mode:
        transformed_endpoints: int
        partition_bits: int
        endpoint_bits: int
        delta_bits: tuple[int, int, int]

    @dataclass
    class RFmt:
        var: str
        a: int
        b: int | None = None

        def read(self, data, pos, start):
            if (self.b is None):
                return getbit(data, pos, start) << self.a

            if (self.a >= self.b):
                bits = getbits(data, pos, start, self.a - self.b + 1)
                return bits << self.b
            else:
                bits = 0
                for i in range(self.b - self.a + 1):
                    bit = getbit(data, pos, start)
                    bits = bits << 1 | bit
                return bits << self.a
    id = 0x1F

    # Table.MF
    modes = (
        Mode(1, 5, 10, (5, 5, 5)),
        Mode(1, 5, 7, (6, 6, 6)),
        Mode(1, 5, 11, (5, 4, 4)),
        Mode(1, 5, 11, (4, 5, 4)),
        Mode(1, 5, 11, (4, 4, 5)),
        Mode(1, 5, 9, (5, 5, 5)),
        Mode(1, 5, 8, (6, 5, 5)),
        Mode(1, 5, 8, (5, 6, 5)),
        Mode(1, 5, 8, (5, 5, 6)),
        Mode(0, 5, 6, (6, 6, 6)),
        Mode(0, 0, 10, (10, 10, 10)),
        Mode(1, 0, 11, (9, 9, 9)),
        Mode(1, 0, 12, (8, 8, 8)),
        Mode(1, 0, 16, (4, 4, 4))
    )

    # Table.F Encoded as bytes.
    #
    # Edited from Pillow/src/libImaging/BcnDecode.c
    # Top 4 bits is the endpoint, bottom 4 bits is the bit to write to
    bit_packings = (
        bytes((116, 132, 180, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20,
               21, 22, 23, 24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48,
               49, 50, 51, 52, 164, 112, 113, 114, 115, 64, 65, 66, 67, 68,
               176, 160, 161, 162, 163, 80, 81, 82, 83, 84, 177, 128, 129, 130,
               131, 96, 97, 98, 99, 100, 178, 144, 145, 146, 147, 148, 179)),
        bytes((117, 164, 165, 0, 1, 2, 3, 4, 5, 6, 176, 177, 132, 16, 17, 18,
               19, 20, 21, 22, 133, 178, 116, 32, 33, 34, 35, 36, 37, 38, 179,
               181, 180, 48, 49, 50, 51, 52, 53, 112, 113, 114, 115, 64, 65,
               66, 67, 68, 69, 160, 161, 162, 163, 80, 81, 82, 83, 84, 85, 128,
               129, 130, 131, 96, 97, 98, 99, 100, 101, 144, 145, 146, 147,
               148, 149)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               52, 10, 112, 113, 114, 115, 64, 65, 66, 67, 26, 176, 160, 161,
               162, 163, 80, 81, 82, 83, 42, 177, 128, 129, 130, 131, 96, 97,
               98, 99, 100, 178, 144, 145, 146, 147, 148, 179)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               10, 164, 112, 113, 114, 115, 64, 65, 66, 67, 68, 26, 160, 161,
               162, 163, 80, 81, 82, 83, 42, 177, 128, 129, 130, 131, 96, 97,
               98, 99, 176, 178, 144, 145, 146, 147, 116, 179)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               10, 132, 112, 113, 114, 115, 64, 65, 66, 67, 26, 176, 160, 161,
               162, 163, 80, 81, 82, 83, 84, 42, 128, 129, 130, 131, 96, 97,
               98, 99, 177, 178, 144, 145, 146, 147, 180, 179)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 132, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 116, 32, 33, 34, 35, 36, 37, 38, 39, 40, 180, 48, 49, 50,
               51, 52, 164, 112, 113, 114, 115, 64, 65, 66, 67, 68, 176, 160,
               161, 162, 163, 80, 81, 82, 83, 84, 177, 128, 129, 130, 131, 96,
               97, 98, 99, 100, 178, 144, 145, 146, 147, 148, 179)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 164, 132, 16, 17, 18, 19, 20, 21, 22,
               23, 178, 116, 32, 33, 34, 35, 36, 37, 38, 39, 179, 180, 48, 49,
               50, 51, 52, 53, 112, 113, 114, 115, 64, 65, 66, 67, 68, 176,
               160, 161, 162, 163, 80, 81, 82, 83, 84, 177, 128, 129, 130, 131,
               96, 97, 98, 99, 100, 101, 144, 145, 146, 147, 148, 149)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 176, 132, 16, 17, 18, 19, 20, 21, 22,
               23, 117, 116, 32, 33, 34, 35, 36, 37, 38, 39, 165, 180, 48, 49,
               50, 51, 52, 164, 112, 113, 114, 115, 64, 65, 66, 67, 68, 69,
               160, 161, 162, 163, 80, 81, 82, 83, 84, 177, 128, 129, 130, 131,
               96, 97, 98, 99, 100, 178, 144, 145, 146, 147, 148, 179)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 177, 132, 16, 17, 18, 19, 20, 21, 22,
               23, 133, 116, 32, 33, 34, 35, 36, 37, 38, 39, 181, 180, 48, 49,
               50, 51, 52, 164, 112, 113, 114, 115, 64, 65, 66, 67, 68, 176,
               160, 161, 162, 163, 80, 81, 82, 83, 84, 85, 128, 129, 130, 131,
               96, 97, 98, 99, 100, 178, 144, 145, 146, 147, 148, 179)),
        bytes((0, 1, 2, 3, 4, 5, 164, 176, 177, 132, 16, 17, 18, 19, 20, 21,
               117, 133, 178, 116, 32, 33, 34, 35, 36, 37, 165, 179, 181, 180,
               48, 49, 50, 51, 52, 53, 112, 113, 114, 115, 64, 65, 66, 67, 68,
               69, 160, 161, 162, 163, 80, 81, 82, 83, 84, 85, 128, 129, 130,
               131, 96, 97, 98, 99, 100, 101, 144, 145, 146, 147, 148, 149)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               52, 53, 54, 55, 56, 57, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73,
               80, 81, 82, 83, 84, 85, 86, 87, 88, 89)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               52, 53, 54, 55, 56, 10, 64, 65, 66, 67, 68, 69, 70, 71, 72, 26,
               80, 81, 82, 83, 84, 85, 86, 87, 88, 42)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               52, 53, 54, 55, 11, 10, 64, 65, 66, 67, 68, 69, 70, 71, 27, 26,
               80, 81, 82, 83, 84, 85, 86, 87, 43, 42)),
        bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23,
               24, 25, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 48, 49, 50, 51,
               15, 14, 13, 12, 11, 10, 64, 65, 66, 67, 31, 30, 29, 28, 27, 26,
               80, 81, 82, 83, 47, 46, 45, 44, 43, 42))
    )

    col_to_int = {
        'r': 0,
        'g': 1,
        'b': 2
    }

    def decompress(self, tex):
        data = tex.mip_data
        width = tex.width
        height = tex.height
        signed = True if tex.fmt_dtype == 0x05 else False
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
        return self.decomp_bc6(data, width, height, signed)

    @staticmethod
    def decomp_bc6(data, width, height, signed: bool):
        h = (height + 3) // 4
        w = (width + 3) // 4
        output: list[int] = [0] * (width * height * 3)
        pos = 0

        for y in range(h):
            for x in range(w):
                block = BC6.bc6_block(data, pos, signed)
                pos += 16

                for ty in range(4):
                    for tx in range(4):
                        ooffs = (x * 4 + tx + (y * 4 + ty) * width) * 3
                        color = block[tx + ty * 4]

                        output[ooffs] = color[0]
                        output[ooffs + 1] = color[1]
                        output[ooffs + 2] = color[2]
        return tuple(output)

    @staticmethod
    def decodepixels(data):
        values = np.array(data, dtype=np.int16).view(np.float16)
        rgba = np.empty(len(data) // 3 * 4, dtype=np.float16)

        rgba[0::4] = values[0::3]
        rgba[1::4] = values[1::3]
        rgba[2::4] = values[2::3]
        rgba[3::4] = 1

        return rgba

    @staticmethod
    def bc6_block(data, pos, signed: bool):
        endpoints = [0] * 12
        ueps = [0] * 12
        block = [(0,) * 3 for x in range(16)]

        startbit = [0]
        mode = getbits(data, pos, startbit, 2)

        epbits = 75
        ib = 3
        cw = aweights3

        if (mode != 0 and mode != 1):
            mode = (getbits(data, pos, startbit, 3) << 2) | mode

            if ((mode & 3) == 2):
                mode = 2 + (mode >> 2)
                epbits = 72
            else:
                mode = 10 + (mode >> 2)
                epbits = 60
                ib = 4
                cw = aweights4

        if (mode >= 14):
            return block

        info = BC6.modes[mode]
        numep = 12 if info.partition_bits else 6

        for i in range(epbits):
            di = BC6.bit_packings[mode][i]
            dw = di >> 4
            di &= 15
            endpoints[dw] |= getbit(data, pos, startbit) << di

        partition = getbits(data, pos, startbit, info.partition_bits)
        # If a float block has no partition bits, then it is a
        # single-subset block. If it has partition bits, then it is a 2
        # subset block

        if (signed):
            BC6.sign_extend(endpoints, 0, info.endpoint_bits)
            BC6.sign_extend(endpoints, 1, info.endpoint_bits)
            BC6.sign_extend(endpoints, 2, info.endpoint_bits)

        if (signed or info.transformed_endpoints):
            for i in range(3, numep, 3):
                BC6.sign_extend(endpoints, i, info.delta_bits[0])
                BC6.sign_extend(endpoints, i + 1, info.delta_bits[1])
                BC6.sign_extend(endpoints, i + 2, info.delta_bits[2])

        if info.transformed_endpoints:
            mask = (1 << info.endpoint_bits) - 1
            for i in range(3, numep, 3):
                endpoints[i] = (endpoints[i] + endpoints[0]) & mask
                endpoints[i + 1] = (endpoints[i + 1] + endpoints[1]) & mask
                endpoints[i + 2] = (endpoints[i + 2] + endpoints[2]) & mask

        # Read Indices
        num_subsets = 2 if info.partition_bits else 1

        for i in range(numep):
            ueps[i] = BC6.unquantise(endpoints[i], info.endpoint_bits, signed)

        for i in range(16):
            s = get_subset(num_subsets, partition, i) * 6
            ib2 = ib
            if (i == 0):
                ib2 -= 1
            elif (num_subsets == 2):
                if (i == anchor_table[0][partition]):
                    ib2 -= 1

            if (startbit[0] + ib2 > 128):
                raise IndexError("BC6 decompressor out of range")

            idx = getbits(data, pos, startbit, ib2)

            col = BC6.interp(ueps[s:s + 3], ueps[s + 3:s + 6], cw[idx], signed)

            block[i] = col

        return tuple(block)

    @staticmethod
    def interp(e0, e1, s, signed) -> tuple[int, ...]:
        col = [0] * 3
        t = 64 - s
        r = (e0[0] * t + e1[0] * s) >> 6
        g = (e0[1] * t + e1[1] * s) >> 6
        b = (e0[2] * t + e1[2] * s) >> 6
        col[0] = BC6.finalize(r, signed)
        col[1] = BC6.finalize(g, signed)
        col[2] = BC6.finalize(b, signed)
        return tuple(col)

    @staticmethod
    def sign_extend(endpoints: list[int], idx: int, prec: int):
        endpoints[idx] = ((~0 << prec)
                          if (endpoints[idx] & (1 << (prec - 1))) != 0
                          else 0) | endpoints[idx]

    @staticmethod
    def unquantise(comp, EPB, signed):
        if (signed):
            s = 0
            if (EPB >= 16):
                unq = comp
            else:
                if (comp < 0):
                    s = 1
                    comp = -comp

                if (comp == 0):
                    unq = 0
                elif (comp >= ((1 << (EPB - 1)) - 1)):
                    unq = 0x7FFF
                else:
                    unq = ((comp << 15) + 0x4000) >> (EPB - 1)

                if (s):
                    unq = -unq
        else:
            if (EPB >= 15):
                unq = comp
            elif (comp == 0):
                unq = 0
            elif (comp == ((1 << EPB) - 1)):
                unq = 0xFFFF
            else:
                unq = ((comp << 15) + 0x4000) >> (EPB - 1)
        return unq

    @staticmethod
    def finalize(val: int, signed: bool):
        if signed:
            if (val < 0):
                return ((-val * 31) >> 5)
            else:
                return (val * 31) >> 5
        else:
            return (val * 31) >> 6


# This part is from BC7.cs


class BC7(TextureFormat):

    @dataclass
    class Mode:
        num_subset: int  # Number of subsets in each partition
        partition_bits: int
        rotation_bits: int
        idx_sel_bits: int  # Index selection bits
        color_bits: int
        alpha_bits: int
        end_pbits: int  # Endpoint P-bits
        shared_pbits: int
        idx_bpe: int  # Index bits per element
        idx_bpe2: int  # Secondary index bits per element

    modes = [
        # Mode 0
        Mode(3, 4, 0, 0, 4, 0, 1, 0, 3, 0),
        # Mode 1
        Mode(2, 6, 0, 0, 6, 0, 0, 1, 3, 0),
        # Mode 2
        Mode(3, 6, 0, 0, 5, 0, 0, 0, 2, 0),
        # Mode 3
        Mode(2, 6, 0, 0, 7, 0, 1, 0, 2, 0),
        # Mode 4
        Mode(1, 0, 2, 1, 5, 6, 0, 0, 2, 3),
        # Mode 5
        Mode(1, 0, 2, 0, 7, 8, 0, 0, 2, 2),
        # Mode 6
        Mode(1, 0, 0, 0, 7, 7, 1, 0, 4, 0),
        # Mode 7
        Mode(2, 6, 0, 0, 5, 5, 1, 0, 2, 0),
    ]

    id = 0x20

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
        return self.decomp_bc7(data, width, height)

    @staticmethod
    def decomp_bc7(data, width, height):
        h = (height + 3) // 4
        w = (width + 3) // 4
        output = bytearray(width * height * 4)
        pos = 0

        for y in range(h):
            for x in range(w):
                block = BC7.bc7_block(data, pos)
                pos += 16

                for ty in range(4):
                    for tx in range(4):
                        ooffs = (x * 4 + tx + (y * 4 + ty) * width) * 4
                        color = block[(ty * 4) + tx]

                        output[ooffs] = color[0]
                        output[ooffs + 1] = color[1]
                        output[ooffs + 2] = color[2]
                        output[ooffs + 3] = color[3]
        return bytes(output)

    @staticmethod
    def bc7_block(data, pos) -> list[bytes]:
        start = [0]
        # start is a list so it can be passed as a reference
        while start[0] < 128 and getbit(data, pos, start) == 0:
            pass
        modeval = start[0] - 1
        mode = BC7.modes[modeval]

        cw = get_weights(mode.idx_bpe)
        aw = get_weights(
            mode.idx_bpe2
            if (mode.alpha_bits and mode.idx_bpe2)
            else mode.idx_bpe
        )

        outcolours = [bytes(4)] * 16

        if (modeval < 8):
            num_subset = mode.num_subset
            num_end_points = num_subset << 1
            partition = getbits(data, pos, start, mode.partition_bits)
            rotation = getbits(data, pos, start, mode.rotation_bits)
            idx_sel = getbits(data, pos, start, mode.idx_sel_bits)

            c = [bytearray(4) for x in range(6)]

            # R, G, B, A maps to 0, 1, 2, 3
            for col in range(3):
                for i in range(num_end_points):
                    if (start[0] + mode.color_bits > 128):
                        raise IndexError("BC7 decompressor out of range")
                    c[i][col] = getbits(data, pos, start, mode.color_bits)

            for i in range(num_end_points):
                if (start[0] + mode.alpha_bits > 128):
                    raise IndexError("BC7 decompressor out of range")
                c[i][3] = (255
                           if mode.alpha_bits == 0
                           else getbits(data, pos, start, mode.alpha_bits))

            # Adjust for P bits
            if mode.end_pbits:
                for i in range(num_end_points):
                    if (start[0] > 127):
                        raise IndexError("BC7 decompressor out of range")

                    p = getbit(data, pos, start)

                    c[i][0] = (c[i][0] << 1) | p
                    c[i][1] = (c[i][1] << 1) | p
                    c[i][2] = (c[i][2] << 1) | p
                    if mode.alpha_bits:
                        c[i][3] = (c[i][3] << 1) | p

            elif mode.shared_pbits:
                p = [0, 0]
                p[0] = getbit(data, pos, start)
                p[1] = getbit(data, pos, start)
                for i in range(num_end_points):
                    end = i & 1
                    c[i][0] = (c[i][0] << 1) | p[end]
                    c[i][1] = (c[i][1] << 1) | p[end]
                    c[i][2] = (c[i][2] << 1) | p[end]
                    if mode.alpha_bits:
                        c[i][3] = (c[i][3] << 1) | p[end]

            for i in range(num_end_points):
                c[i] = BC7.unquantise(
                    c[i],
                    mode.color_bits + (mode.end_pbits | mode.shared_pbits),
                    mode.alpha_bits + mode.end_pbits
                )

            # Read colour indices
            cibit = [start[0]]
            aibit = [cibit[0] + 16 * mode.idx_bpe - mode.num_subset]
            for i in range(16):
                s = get_subset(num_subset, partition, i) << 1
                ib = mode.idx_bpe

                if (i == 0):
                    ib -= 1
                elif (mode.num_subset == 2):
                    if (i == anchor_table[0][partition]):
                        ib -= 1
                elif (mode.num_subset == 3):
                    if (i == anchor_table[1][partition]):
                        ib -= 1
                    elif (i == anchor_table[2][partition]):
                        ib -= 1

                if (cibit[0] + ib > 128):
                    raise IndexError("BC7 decompressor out of range")
                i0 = getbits(data, pos, cibit, ib)

                # Read Alpha
                if (mode.alpha_bits and mode.idx_bpe2):
                    ib2 = mode.idx_bpe2
                    if (ib2 and i == 0):
                        ib2 -= 1

                    if (aibit[0] + ib2 > 128):
                        raise IndexError("BC7 decompressor out of range")
                    i1 = getbits(data, pos, aibit, ib2)

                    if (idx_sel):
                        outpixel = BC7.interpolate(c[s:], aw[i1], cw[i0])
                    else:
                        outpixel = BC7.interpolate(c[s:], cw[i0], aw[i1])
                else:
                    outpixel = BC7.interpolate(c[s:], cw[i0], cw[i0])

                match (rotation):
                    case 1:
                        temp = outpixel[0]
                        outpixel[0] = outpixel[3]
                        outpixel[3] = temp
                    case 2:
                        temp = outpixel[1]
                        outpixel[1] = outpixel[3]
                        outpixel[3] = temp
                    case 3:
                        temp = outpixel[2]
                        outpixel[2] = outpixel[3]
                        outpixel[3] = temp
                outcolours[i] = bytes(outpixel)
            return outcolours
        return outcolours

    @staticmethod
    def unquantise_ch(r1: int, r2: int) -> int:
        temp = r1 << (8 - r2)
        return temp | (temp >> r2)

    @staticmethod
    def unquantise(color: bytearray, col_bits: int, alpha_bits: int) -> bytearray:
        temp = bytearray(4)
        for i in range(3):
            temp[i] = BC7.unquantise_ch(color[i], col_bits)

        temp[3] = (BC7.unquantise_ch(color[3], alpha_bits)
                   if alpha_bits > 0
                   else 255)
        return temp

    @staticmethod
    def interpolate(
            e: list[bytearray], s0: int, s1: int) -> bytearray:
        temp = bytearray(4)
        t0 = 64 - s0
        t1 = 64 - s1
        temp[0] = ((t0 * e[0][0] + s0 * e[1][0] + 32) >> 6)
        temp[1] = ((t0 * e[0][1] + s0 * e[1][1] + 32) >> 6)
        temp[2] = ((t0 * e[0][2] + s0 * e[1][2] + 32) >> 6)
        temp[3] = ((t1 * e[0][3] + s1 * e[1][3] + 32) >> 6)
        return temp
