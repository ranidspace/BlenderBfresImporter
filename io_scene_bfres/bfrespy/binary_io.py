""" Code referenced from Syroot/io_scene_bfres licensed unfer MIT"""
from __future__ import annotations
import io
import struct
import numpy


class BinaryReader:
    """A wrapper to read binary data as other formats"""

    def __init__(
            self,
            stream: io.BytesIO | io.BufferedReader,
            leave_open=False):
        self.endianness: str
        self.leave_open = leave_open
        self.stream = stream

        if (type(stream) is bytes):
            stream = io.BytesIO(stream)
            return super().__init__(stream)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if (self.leave_open is False):
            self.stream.close()
        else:
            print("nothing happened")
            return

    def temporary_seek(self, offset=None, origin=None):
        if (offset is None):
            offset = 0
        if (origin is None):
            origin = io.SEEK_CUR
        return NewSeek(self, offset, origin)

    def align(self, alignment):
        self.seek(-self.tell() % alignment, io.SEEK_CUR)

    def seek(self, offset, whence=io.SEEK_CUR):
        return self.stream.seek(offset, whence)

    def tell(self):
        return self.stream.tell()

    def read_null_string(self, encoding=None) -> str:
        # Mostly the same as ascii i dont think there's harm in setting this?
        encoding = encoding if encoding is not None else 'utf-8'
        text = bytearray()
        i = self.stream.read(1)
        while i[0] != 0:
            text += i
            i = self.stream.read(1)
        text = text.decode(encoding)
        return text

    # Unsigned

    def read_byte(self) -> int:
        return self.stream.read(1)[0]

    def read_bytes(self, count) -> bytes:
        return self.stream.read(count)

    def read_uint16(self) -> int:
        return struct.unpack(self.endianness + 'H',
                             self.stream.read(2))[0]

    def read_uint16s(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'H',
                             self.stream.read(2 * count))

    def read_uint32(self) -> int:
        return struct.unpack(self.endianness + 'I',
                             self.stream.read(4))[0]

    def read_uint32s(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'I',
                             self.stream.read(4 * count))

    def read_uint64(self) -> int:  # Switch has 64 bit offsets
        return struct.unpack(self.endianness + 'Q',
                             self.stream.read(8))[0]

    def read_uint64s(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'Q',
                             self.stream.read(8 * count))

    # Signed

    def read_int16(self) -> int:
        return struct.unpack(self.endianness + 'h',
                             self.stream.read(2))[0]

    def read_int16s(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'h',
                             self.stream.read(2 * count))

    def read_int32(self) -> int:
        return struct.unpack(self.endianness + 'i',
                             self.stream.read(4))[0]

    def read_int32s(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'i',
                             self.stream.read(4 * count))

    def read_int64(self) -> int:
        return struct.unpack(self.endianness + 'q',
                             self.stream.read(8))[0]

    def read_int64s(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'q',
                             self.stream.read(8 * count))

    def read_sbyte(self) -> int:
        return struct.unpack(self.endianness + 'b',
                             self.stream.read(1))[0]

    def read_sbytes(self, count) -> tuple[int, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'b',
                             self.stream.read(1 * count))

    # Other Formats

    def read_bool(self) -> bool:
        return bool(struct.unpack(self.endianness + '?',
                                  self.stream.read(1))[0])

    def read_bools(self, count) -> tuple[bool, ...]:
        return struct.unpack(self.endianness + str(int(count)) + '?',
                             self.stream.read(count))

    def read_single(self) -> float:
        return struct.unpack(self.endianness + 'f',
                             self.stream.read(4))[0]

    def read_singles(self, count) -> tuple[float, ...]:
        return struct.unpack(self.endianness + str(int(count)) + 'f',
                             self.stream.read(4 * count))

    def read_raw_string(self, length, encoding=None) -> str:
        encoding = encoding if encoding is not None else 'utf-8'
        return self.stream.read(length).decode(encoding)

    def read_matrix_3x4(self) -> numpy.ndarray:
        return numpy.reshape(self.read_singles(12), (3, 4))

    def read_matrix_3x4s(self, count) -> list[numpy.ndarray]:
        values = []
        for i in range(count):
            values.append(self.read_matrix_3x4())
        return values

    # Type hinting is mostly just for fun but this genuinely bothered me that
    # you couldnt add set lengths, you have to just write it a bunch of times.
    def read_vector2f(self) -> tuple[float, float]:
        return (self.read_single(), self.read_single())

    def read_vector3f(self) -> tuple[float, float, float]:
        return (self.read_single(), self.read_single(), self.read_single())

    def read_vector4f(self) -> tuple[float, float, float, float]:
        return (self.read_single(), self.read_single(),
                self.read_single(), self.read_single())

    def read_bounding(self):
        """Reads a Bounding instance from the current stream
        and returns it.
        """
        from .models.shape import Bounding
        return Bounding(self.read_vector3f(), self.read_vector3f())

    def read_boundings(self, count):
        """Reads Bounding instances from the current stream
        and returns them.
        """
        values = []
        for i in range(count):
            values.append(self.read_bounding())
        return values

    def read_decimal10x5(self):
        from .common import Decimal10x5
        return Decimal10x5(self.read_uint16(), raw=True)


class NewSeek:
    """Temporarily move the pointer to a different location and return it
    to the correct position when it's closed
    """

    def __init__(self, reader: BinaryReader, offset, whence):
        self.offset = offset
        self.whence = whence
        self.reader = reader
        self.prev_pos = reader.tell()

    def __enter__(self):
        if (self.offset is not None):
            self.reader.seek(self.offset, self.whence)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.reader.seek(self.prev_pos, io.SEEK_SET)


class BinaryWriter:
    def __init__(self, raw):
        self.raw = raw
        self.endianness = '<'  # Little-endian

    def __enter__(self):
        self.writer = io.BufferedWriter(self.raw)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.writer.close()

    def align(self, alignment):
        self.writer.seek(-self.writer.tell() % alignment, io.SEEK_CUR)

    def reserve_offset(self):
        return Offset(self)

    def satisfy_offset(self, offset, value=None):
        offset.satisfy(self, value)

    def seek(self, offset, whence=io.SEEK_SET):
        self.writer.seek(offset, whence)

    def tell(self):
        return self.writer.tell()

    def write_0_string(self, value, encoding='ascii'):
        self.write_raw_string(value, encoding)
        self.write_byte(0)

    def write_byte(self, value):
        self.writer.write(struct.pack('B',
                                      value))

    def write_bytes(self, value):
        self.writer.write(value)

    def write_int32(self, value):
        self.writer.write(struct.pack(self.endianness + 'i',
                                      value))

    def write_int32s(self, value):
        self.writer.write(struct.pack(self.endianness + str(len(value)) + 'i',
                                      *value))

    def write_sbyte(self, value):
        self.writer.write(struct.pack(self.endianness + 'b',
                                      value))

    def write_sbytes(self, value):
        self.writer.write(struct.pack(self.endianness + str(len(value)) + 'b',
                                      *value))

    def write_single(self, value):
        self.writer.write(struct.pack(self.endianness + 'f',
                                      value))

    def write_singles(self, value):
        self.writer.write(struct.pack(self.endianness + str(len(value)) + 'f',
                                      *value))

    def write_uint16(self, value):
        self.writer.write(struct.pack(self.endianness + 'H',
                                      value))

    def write_uint16s(self, value):
        self.writer.write(struct.pack(self.endianness + str(len(value)) + 'H',
                                      *value))

    def write_uint32(self, value):
        self.writer.write(struct.pack(self.endianness + 'I',
                                      value))

    def write_uint32s(self, value):
        self.writer.write(struct.pack(self.endianness + str(len(value)) + 'I',
                                      *value))

    def write_raw_string(self, value, encoding='ascii'):
        self.writer.write(bytearray(value, encoding))


class Offset:
    def __init__(self, writer):
        # Remember the position of the offset to change it later.
        self.position = writer.tell()
        # Write an empty offset for now.
        self.value = 0
        writer.write_uint32(self.value)

    def satisfy(self, writer, value=None):
        self.value = value if value else writer.tell()
        # Seek back temporarily to the offset position to write the final
        # offset value.
        current_position = writer.tell()
        writer.seek(self.position)
        writer.write_uint32(self.value)
        writer.seek(current_position)
