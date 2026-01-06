from __future__ import annotations
import io
from abc import ABC, abstractmethod
from typing import TypeVar
from collections.abc import Callable
from . import binary_io as bin_io


class ResData(ABC):
    """Represents the common interface for ResFile data instances."""
    @abstractmethod
    def load(self, loader):
        """Loads raw data from the loader data stream into instances"""
        pass


_I = TypeVar('_I', bound=ResData)
_T = TypeVar('_T')


class ResFileLoader(bin_io.BinaryReader):
    """Loads the hierachy and data of a Bfres ResFile"""

    def __init__(self, res_file, stream: io.BytesIO | io.BufferedReader,
                 leave_open=False, res_data: ResData | None = None):
        super().__init__(stream, leave_open)
        self.res_file = res_file
        self._data_map = {}
        self.is_switch: bool
        if (res_data):
            self.importable_file = res_data

    # Internal Methods

    def _import_section(self, raw=None, res_data=None, res_file=None):
        if raw and res_data and res_file:
            platform_switch = False

            with bin_io.BinaryReader(raw) as reader:
                reader.seek(24, io.SEEK_SET)
                platform_switch = reader.read_uint32 != 0

            if (platform_switch):
                from .switch.switchcore import ResFileSwitchLoader
                with ResFileSwitchLoader(res_file, raw, res_data) as reader:
                    reader._import_section()
        else:
            self.__read_imported_file_header()
            from .import models
            if isinstance(self.importable_file, models.Shape):
                shape_offs = self.read_uint32()
                vtx_buff_offs = self.read_uint32()

                self.seek(shape_offs, io.SEEK_SET)
                self.importable_file.load(self)

                self.seek(vtx_buff_offs, io.SEEK_SET)
                buffer = models.VertexBuffer()
                buffer.load(self)
                self.importable_file.vtx_buffer = buffer
            else:
                self.importable_file.load(self)

    def __read_imported_file_header(self):
        self.endianness = '>'
        self.seek(8, io.SEEK_SET)
        self.res_file.version = self.read_uint32()
        self.res_file.set_version_info(self.res_file.version)

    def _read_byte_order(self) -> str:
        self.endianness = '>'
        bom = self.__byte_order[self.read_uint16()]
        self.endianness = bom
        return bom

    __byte_order = {
        0xFEFF: '>',
        0xFFFE: '<',
    }

    def _execute(self):
        """Starts deserializing the data from the ResFile root."""
        self.res_file.load(self)

    def load(self, _I: type[_I], use_offset=True) -> _I:
        """Reads and returns an ResData instance of type _I from the following
        offset or returns None if the read offset is 0.
        """
        if (not use_offset):
            return self.__read_res_data(_I)
        offset = self.read_offset()
        if (offset == 0):
            return _I()
        with self.temporary_seek(offset, io.SEEK_SET):
            return self.__read_res_data(_I)

    # When blender updates to python >3.12 you can do:
    # def load_custom[_T](self, callback: Callable[[], _T], offset=None) -> _T:
    # and then return _T()
    def load_custom(self, typ: type[_T],
                    callback: Callable[[], _T], offset=None) -> _T:
        """Reads and returns an instance of arbitrary type _I from the following
        offset with the given callback or returns None if the read offset is 0.
        """
        offset = self.read_offset() if offset is None else offset
        if (offset == 0):
            return typ()
        with (self.temporary_seek(offset, io.SEEK_SET)):
            return callback()

    def load_dict(self, _I):
        """Reads and returns a ResDict instance with elements of type _I from
        the following offset or returns an empty instance if the read offset
        is 0.
        """
        from .common import ResDict

        offset = self.read_offset()
        if (offset == 0):
            return ResDict()

        with self.temporary_seek(offset, io.SEEK_SET):
            dict = ResDict()
            dict.load(_I, self)
            return dict

    def load_list(self, _I, count, offset=None):
        """Reads and returns a List instance with elements of type _I and
        a length of the count.
        """
        list_ = []
        offset = self.read_offset() if offset is None else offset
        if (offset == 0 or count == 0):
            return []
        with self.temporary_seek(offset, io.SEEK_SET):
            while count > 0:
                list_.append(self.__read_res_data(_I))
                count -= 1
            return list_

    def load_string(self, encoding=None) -> str:
        """Reads and returns a str instance from the following offset or an
        empty string if the read offset is 0.
        """
        from . import common
        offset = self.read_offset()
        if (offset == 0):
            return ''
        if (offset in common.stringcache):
            return common.stringcache[offset]
        with self.temporary_seek(offset, io.SEEK_SET):
            return self.read_string(encoding)

    def load_strings(self, count, encoding=None) -> tuple[str, ...]:
        """Reads and returns count of str from the following offset.
        """
        from . import common
        offsets = self.read_offsets(count)
        names = [''] * len(offsets)
        with self.temporary_seek():
            for i, offset in enumerate(offsets):
                if (offset == 0):
                    continue
                if (offset in common.stringcache):
                    names[i] = common.stringcache[offset]
                self.seek(offset, io.SEEK_SET)
                names[i] = self.read_string(encoding)
        return tuple(names)

    def load_dict_values(self, _I: type[ResData],
                         dict_offs=None, values_offs=None):
        """Reads and returns a ResDict instance with elements of type _I from
        the following offset or returns an empty instance if the
        read offset is 0.
        """
        from .common import ResDict
        if (dict_offs is None or values_offs is None):
            values_offs = self.read_offset()
            dict_offs = self.read_offset()
        if (dict_offs == 0):
            return ResDict()
        with self.temporary_seek(dict_offs, io.SEEK_SET):
            dict_ = ResDict()
            dict_.load(_I, self)

            keys = list(dict_.keys())
            values = self.load_list(_I, len(dict_), values_offs)

            dict_.clear()
            for i in range(len(keys)):
                dict_.append(keys[i], values[i])
            return dict_

    def load_relocation_table(self, offset):
        from .rlt import RelocationTable
        with self.temporary_seek(offset, io.SEEK_SET):
            self.relocation_table = self.__read_res_data(RelocationTable)

    def read_size(self):
        return self.read_uint32()

    def read_string(self, encoding):
        return self.read_null_string(encoding)

    def _check_signature(self, valid_signature):
        """Reads a BFRES signature consisting of 4 ASCII characters encoded as
        a UINT32 and checks for validity.
        """
        signature = self.read_raw_string(4, 'ascii')
        if (signature != valid_signature):
            print(f"Invalid signature, expected '{valid_signature}' but got "
                  f"'{signature}' at position {self.tell()}.")

    def read_offset(self):
        """Reads a BFRES offset which is relative to itself,
        and returns the absolute address."""
        offset = self.read_uint32()
        return 0 if offset == 0 else self.tell() - 4 + offset

    def read_offsets(self, count) -> tuple[int, ...]:
        """Reads BFRES offsets which are relative to themselves,
        and returns the absolute addresses.
        """
        values = [] * count
        for i in range(count):
            values.append(self.read_offset())
        return tuple(values)

    def read_bit32_bools(self, count) -> tuple[bool, ...]:
        booleans = [None] * count
        if (count == 0):
            return booleans
        idx = 0
        while (idx < count):
            value = self.read_uint32()
            for i in range(32):
                if (count <= idx):
                    break
                booleans[idx] = (value & 0x1) != 0
                value >>= 1

                idx += 1
        return tuple(booleans)

    def load_header_block(self):
        # This should never be run, only ResFileSwitchLoader uses it, added
        # this just to keep errors from occurring
        raise NotImplementedError(
            "Tried to load a header block on a non-switch loader"
        )

    # Private Methods

    def __read_res_data(self, _I: type[_I]) -> _I:
        offset = self.tell()
        instance = _I()
        instance.load(self)

        existing_instance = self._data_map.get(offset)
        if existing_instance:
            return existing_instance
        else:
            self._data_map[offset] = instance
            return instance

# Byte/Uint32 Extensions


def _decode(byte, first_bit, bits):
    """Returns a int instance represented by the given number of bits,
    starting at the first_bit.
    """
    return ((byte >> first_bit) & ((1 << bits) - 1))


def _encode(byte, value, first_bit, bits):
    """Returns the current int with the given value set into the given number
    of bits starting at first_bit
    """
    value = int(value)
    mask = (((1 << bits) - 1) << first_bit)
    byte &= ~mask
    value = (value << first_bit) & mask
    return (byte | value)


def enable_bit(byte, index):
    """Returns the current int with the bit at the index set (being 1)."""
    return byte | (1 << index)


def disable_bit(byte, index):
    """Returns the current int with the bit at the index cleared (being 0)."""
    return byte & ~(1 << index)


def get_bit(byte, index):
    """Returns a value indicating whether the bit at the index in the current
    Byte is enabled or disabled.
    """
    return (byte & (1 << index)) != 0


def set_bit(byte, index: int, enable: bool):
    """Returns the current Byte with the bit at the index enabled or disabled,
    according to enable."""
    if (enable):
        return enable_bit(byte, index)
    else:
        return disable_bit(byte, index)
