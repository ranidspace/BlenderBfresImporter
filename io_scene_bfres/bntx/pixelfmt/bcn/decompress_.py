# This file is inspired by many different libraries, including the python "pillow" module, the rust "block_compression"
# crate, the implementation in Switch Toolbox.
from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt


def vector_decode_c01(arr: npt.NDArray[np.uint16]) -> npt.NDArray[np.uint32]:
    # R[15:11] G[10:5] B[4:0]
    # OFFTOPIC: Did you know the human eye is more sensitive to green? Which is why it gets the extra bit here
    rgb565 = np.dstack(((arr >> 11) & 0x1F, (arr >> 5) & 0x3F, arr & 0x001F, np.full(arr.shape, 0xFF, dtype=int)))
    rgb888 = rgb565.astype(np.uint32)

    rgb888[..., 0::2] = (rgb888[..., 0::2] * 527 + 23) >> 6
    rgb888[..., 1] = (rgb888[..., 1] * 259 + 33) >> 6
    return rgb888


def vector_decode_c23(
    reference: npt.NDArray[np.uint16],
    colors: npt.NDArray[np.uint32],
    not_bc1: bool,
) -> npt.NDArray[np.uint8]:

    c0 = reference[..., 0, np.newaxis].repeat(4, axis=-1)
    c1 = reference[..., 1, np.newaxis].repeat(4, axis=-1)

    # c2
    c2 = np.where(
        not_bc1 | (c0 > c1),
        (2 * colors[..., 0, :] + colors[..., 1, :]) // 3,
        (colors[..., 0, :] + colors[..., 1, :]) // 2,
    )
    c2[..., 3] = 0xFF

    # c3
    c3 = np.where(not_bc1 | (c0 > c1), (colors[..., 0, :] + 2 * colors[..., 1, :]) // 3, 0)
    c3[..., 3] = np.where(not_bc1 | (reference[..., 0] > reference[..., 1]), 0xFF, 0x00)

    return np.hstack((colors, c2[:, np.newaxis, :], c3[:, np.newaxis, :])).astype(np.uint8)


def decode_color_blocks(blocks: npt.NDArray, not_bc1: bool):
    colors = vector_decode_c01(blocks["ref_col"])
    colors = vector_decode_c23(blocks["ref_col"], colors, not_bc1)

    shift = np.arange(0, 32, 2, dtype=np.uint8)
    row_indices = np.arange(blocks.shape[0])[:, np.newaxis]
    return colors[row_indices, (blocks["idx_bits"][..., np.newaxis] >> shift) & 3]


def decode_alpha_blocks(blocks: npt.NDArray, snorm: bool) -> npt.NDArray[np.float32]:
    work_blocks = blocks.astype(np.float32)
    if snorm:
        work_blocks = np.where(work_blocks == -128.0, -1.0, work_blocks / 127.0)
    else:
        work_blocks /= 255.0

    range0 = np.arange(6.0, 0.0, -1.0)
    range1 = np.arange(1.0, 7.0)

    range2 = np.pad(np.arange(4.0, 0.0, -1.0), (0, 2))
    range3 = np.pad(np.arange(1.0, 5.0), (0, 2))

    last = np.array([-1.0, 1.0]) if snorm else np.array([0.0, 1.0])

    work_blocks = np.concatenate(
        (
            work_blocks,
            np.where(
                work_blocks[..., 0, np.newaxis].repeat(6, axis=-1) > work_blocks[..., 1, np.newaxis].repeat(6, axis=-1),
                (work_blocks[..., 0, np.newaxis] * range0 + work_blocks[..., 1, np.newaxis] * range1) / 7.0,
                (work_blocks[..., 0, np.newaxis] * range2 + work_blocks[..., 1, np.newaxis] * range3) / 5.0,
            ),
        ),
        axis=-1,
    )
    work_blocks[..., 6:8] = np.where(
        work_blocks[..., 0, np.newaxis].repeat(2, axis=-1) > work_blocks[..., 1, np.newaxis].repeat(2, axis=-1),
        work_blocks[..., 6:8],
        last,
    )
    return work_blocks


def decomp_bc1(data, width, height):
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    dt = np.dtype({"names": ["ref_col", "idx_bits"], "formats": ["2<u2", "<u4"]})
    blocks = np.frombuffer(data, dtype=dt)

    outblocks = decode_color_blocks(blocks, not_bc1=False)
    outblocks = outblocks.reshape(h, w, 4, 4, 4).swapaxes(1, 2).reshape(h * 4, w * 4, 4)

    return outblocks[:height, :width]


def decomp_bc2(data, width, height):
    # XXX: Untested code, dont know any models which use BC2 textures
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    dt = np.dtype({"names": ["alphadata", "ref_col", "idx_bits"], "formats": ["<u8", "2<u2", "<u4"]})
    blocks = np.frombuffer(data, dtype=dt)

    outblocks = decode_color_blocks(blocks, not_bc1=True)

    shift = np.arange(0, 64, 4, dtype=np.uint8)
    outblocks[..., 3] = ((blocks["alphadata"][..., np.newaxis, :] >> shift) & 0xF) * 17
    outblocks = outblocks.reshape(h, w, 4, 4, 4).swapaxes(1, 2).reshape(h * 4, w * 4, 4)

    return outblocks[:height, :width]


def decomp_bc3(data, width, height):
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    dt = np.dtype({"names": ["alphadata", "ref_col", "idx_bits"], "formats": ["<u8", "2<u2", "<u4"]})
    blocks = np.frombuffer(data, dtype=dt)

    col_blocks = decode_color_blocks(blocks, not_bc1=True).astype(np.float32) / 255.0
    alpha_select = blocks["alphadata"] >> 16

    alpha_blocks = np.stack((blocks["alphadata"] & 0xFF, (blocks["alphadata"] >> 8) & 0xFF), axis=-1)
    alpha_blocks = decode_alpha_blocks(alpha_blocks, snorm=False)

    shift = np.arange(0, 48, 3, dtype=np.uint8)
    row_indices = np.arange(alpha_blocks.shape[0])[:, np.newaxis]
    col_blocks[..., 3] = alpha_blocks[row_indices, (alpha_select[..., np.newaxis] >> shift) & 7]

    col_blocks = col_blocks.reshape(h, w, 4, 4, 4).swapaxes(1, 2).reshape(h * 4, w * 4, 4)

    return col_blocks[:height, :width]


def decomp_bc4(data, width, height, snorm):
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    dtype = np.int8 if snorm else np.uint8

    blocks = np.stack((np.frombuffer(data[::8], dtype=dtype), np.frombuffer(data[1::8], dtype=dtype)), axis=-1)

    blocks = decode_alpha_blocks(blocks, snorm)

    outblocks = np.empty((w * h, 16), dtype=np.float32)
    shift = np.arange(0, 48, 3, dtype=dtype)

    select = np.frombuffer(data, dtype="<u8") >> 16

    row_indices = np.arange(blocks.shape[0])[:, np.newaxis]
    outblocks = blocks[row_indices, (select[..., np.newaxis] >> shift) & 7]
    outblocks = outblocks.reshape(h, w, 4, 4).swapaxes(1, 2).reshape(h * 4, w * 4)

    return outblocks[:height, :width]


def decomp_bc5(data, width, height, snorm) -> npt.NDArray[np.int8]:
    h = math.ceil(height / 4)
    w = math.ceil(width / 4)

    dtype = np.int8 if snorm else np.uint8
    # For every block, 2 components (red and green), and 8 colours
    blocks = np.empty((w * h, 2, 2), dtype=dtype)
    blocks[:, 0, 0] = np.frombuffer(data[::16], dtype=dtype)
    blocks[:, 0, 1] = np.frombuffer(data[1::16], dtype=dtype)
    blocks[:, 1, 0] = np.frombuffer(data[8::16], dtype=dtype)
    blocks[:, 1, 1] = np.frombuffer(data[9::16], dtype=dtype)

    blocks = decode_alpha_blocks(blocks, snorm)

    outblocks = np.empty((w * h, 16, 2), dtype=np.float32)
    shift = np.arange(0, 48, 3, dtype=dtype)

    select = np.frombuffer(data, dtype="<i8").reshape(w * h, 2) >> 16

    # jesus christ
    row_indices = np.arange(blocks.shape[0])[:, np.newaxis]
    outblocks[..., 0] = blocks[row_indices, 0, (select[..., 0, np.newaxis] >> shift) & 7]
    outblocks[..., 1] = blocks[row_indices, 1, (select[..., 1, np.newaxis] >> shift) & 7]
    outblocks = outblocks.reshape(h, w, 4, 4, 2).swapaxes(1, 2).reshape(h * 4, w * 4, 2)

    if not snorm:
        outblocks = outblocks * 2.0 - 1.0
    return outblocks[:height, :width]
