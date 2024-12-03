# This file is part of botwtools.
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
import numpy as np
from .base import TextureFormat
import logging
log = logging.getLogger(__name__)


class R8(TextureFormat):
    id = 0x02
    bytes_per_pixel = 1

    @staticmethod
    def decodepixels(data):
        pixels = np.frombuffer(data, dtype='B') / 255
        rgba = np.empty((pixels.size * 4), dtype=pixels.dtype)
        rgba[0::4] = pixels
        rgba[1::4] = pixels
        rgba[2::4] = pixels
        rgba[3::4] = 1
        return rgba


class R5G6B5(TextureFormat):
    # XXX untested code, needs confirmation
    id = 0x07
    bytes_per_pixel = 2

    @staticmethod
    def decodepixels(data):
        pixels = np.frombuffer(data, dtype='H')
        r = ((pixels & 0x1F)) / 31
        g = ((pixels >> 5) & 0x3F) / 63
        b = ((pixels >> 11) & 0x1F) / 31
        rgba = np.empty((pixels.size * 4), dtype=r.dtype)
        rgba[0::4] = r
        rgba[1::4] = g
        rgba[2::4] = b
        rgba[3::4] = 1
        return rgba


class R8G8(TextureFormat):
    # XXX untested code, needs confirmation
    id = 0x09
    bytes_per_pixel = 2

    @staticmethod
    def decodepixels(data):
        pixels = np.frombuffer(data, dtype='B') / 255
        rgba = np.empty((pixels.size * 2), dtype=pixels.dtype)
        rgba[0::4] = pixels[0::2]
        rgba[1::4] = pixels[1::2]
        rgba[2::4] = 1
        rgba[3::4] = 1
        return rgba


class R16(TextureFormat):
    # XXX untested code, needs confirmation
    id = 0x0A
    bytes_per_pixel = 2
    depth = 16

    @staticmethod
    def decodepixels(data):
        rgba = np.empty(len(data) * 4, dtype=np.float32)
        rgba[0::4] = np.frombuffer(data, dtype='B') / 65536
        rgba[1::4] = 0
        rgba[2::4] = 0
        rgba[3::4] = 0
        return rgba


class R8G8B8A8(TextureFormat):
    id = 0x0B
    bytes_per_pixel = 4


class R11G11B10(TextureFormat):
    # XXX untested code, needs confirmation
    id = 0x0F
    bytes_per_pixel = 4
    depth = 16

    @staticmethod
    def decodepixels(data):
        pixels = np.frombuffer(data, dtype='I')
        r = (pixels & 0x07FF) / 2047
        g = ((pixels >> 11) & 0x07FF) / 2047
        b = ((pixels >> 22) & 0x03FF) / 1023
        rgba = np.empty((r.size * 4), dtype=r.dtype)
        rgba[0::4] = r
        rgba[1::4] = g
        rgba[2::4] = b
        rgba[3::4] = 1
        return rgba


class R32(TextureFormat):
    # XXX untested code, needs confirmation
    id = 0x14
    bytes_per_pixel = 4
    depth = 32

    @staticmethod
    def decodepixels(data):
        rgba = np.empty((len(data) * 4))
        rgba[0::4] = np.frombuffer(data, dtype='I') / 4294967295
        rgba[1::4] = 0
        rgba[2::4] = 0
        rgba[3::4] = 0
        return rgba
