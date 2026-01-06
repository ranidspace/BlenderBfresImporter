from __future__ import annotations

import io
from dataclasses import dataclass
from functools import singledispatchmethod
from collections.abc import Iterator, Collection
from typing import TypeVar, Generic, overload, Any
from enum import IntEnum, IntFlag

from . import core, texture

T = TypeVar('T', bound=core.ResData)

stringcache: dict[int, str] = {}


class Decimal10x5:
    """Represents a 16-bit fixed-point decimal consisting of 1 sign bit, 10 
    integer bits and 5 fractional bits (denoted as Q10.5). Note that the 
    implementation is not reporting over- and underflowing errors.
    """
    _M = 10
    """Number of integral part bits."""
    _N = 5
    """Number of fractional part bits."""

    def __init__(self, value: int | float, raw=False):
        # Raw reads a Decimal10x5 by it's raw bit represetation
        if (not raw):
            if type(value) is int:
                Decimal10x5(value << self._N, raw=True)
            elif type(value) is float:
                Decimal10x5(round(value * (1 << self._N)), raw=True)

        # When raw is false, it converts an int into Decimal10x5
        elif type(value) is int:
            # unchecked for overflow, but all python ints are.
            self.raw: int = value

    # These are meant to be constants but python doesnt allow referencing the
    # class inside of itself
    @classmethod
    def MAX_VALUE(cls):
        return Decimal10x5(0xFFFF, raw=True)

    @classmethod
    def MIN_VALUE(cls):
        return Decimal10x5(0x0000, raw=True)

    def __hash__(self):
        return self.raw

    def __pos__(self):
        return self

    def __eq__(self, value: object) -> bool:
        if (type(value) is not Decimal10x5):
            return False
        return self.raw == value.raw

    def __neg__(self):
        return Decimal10x5(-self.raw, raw=True)

    def __add__(self, other: Decimal10x5):
        return Decimal10x5(self.raw + other.raw, raw=True)

    def __sub__(self, other: Decimal10x5):
        return Decimal10x5(self.raw - other.raw, raw=True)

    def __mul__(self, other: int | Decimal10x5):
        if type(other) is Decimal10x5:
            k = 1 << (self._N - 1)
            return Decimal10x5((self.raw * other.raw + k) >> self._N, raw=True)
        elif other is int:
            return Decimal10x5(self.raw * other, raw=True)
        else:
            raise TypeError(
                "Decimal10x5 can only be multiplied by int or itself"
            )

    def __truediv__(self, other: int | Decimal10x5):
        if type(other) is Decimal10x5:
            return Decimal10x5((self.raw << self._N) // other.raw, raw=True)
        elif other is int:
            return Decimal10x5(self.raw // other, raw=True)
        else:
            raise TypeError(
                "Decimal10x5 can only be divided by int or itself"
            )

    def __floordiv__(self, other: int | Decimal10x5):
        return (self / other)  # defined by truediv

    def __int__(self):
        k = 1 << (self._N - 1)
        return (self.raw + k) >> self._N

    def __float__(self):
        return self.raw / (1 << self._N)


class AnimCurve(core.ResData):
    """Represents an animation curve used by several sections to control 
    different parameters over time.
    """
    _FLAGS_MASK_FRAME_TYPE = 0B00000000_00000011
    _FLAGS_MASK_KEY_TYPE = 0B00000000_00001100
    _FLAGS_MASK_CURVE_TYPE = 0B00000000_01110000

    def __init__(self):
        self._flags = 0
        self.anim_data_offset = 0
        """The memory offset relative to the start of the corresponding
        animation data structure to animate the field stored at that address.
        Note that enums exist in the specifc animation which map
        offsets to names
        """
        self.start_frame = 0
        """The first frame at which a key is placed."""
        self.end_frame = 0
        """The last frame at which a key is placed."""
        self.scale = 0
        """The scale to multiply values of the curve by."""
        self.offset = 0
        """The offset to add to the values of the curve
        (after multiplicating them).
        """
        self.delta = 0
        """The difference between the lowest and highest key value."""
        self.frames = []
        self.keys = []

    @property
    def frame_type(self) -> AnimCurveFrameType:
        """The data type in which Frames are loaded and saved.
        For simplicity, the class always stores frames as converted Singles.
        """
        return AnimCurveFrameType(self._flags & self._FLAGS_MASK_FRAME_TYPE)

    @frame_type.setter
    def frame_type(self, value: AnimCurveFrameType):
        self._flags &= ~self._FLAGS_MASK_FRAME_TYPE | value

    @property
    def key_type(self) -> AnimCurveKeyType:
        """ The data type in which Keys are loaded and saved.
        The class always stores frames as converted Single Instances.
        """
        return AnimCurveKeyType(self._flags & self._FLAGS_MASK_KEY_TYPE)

    @key_type.setter
    def key_type(self, value: AnimCurveKeyType):
        self._flags &= ~self._FLAGS_MASK_KEY_TYPE | value

    @property
    def curve_type(self) -> AnimCurveType:
        """The curve type, determining the number of elements stored
        with each key.
        """
        return AnimCurveType(self._flags & self._FLAGS_MASK_CURVE_TYPE)

    @curve_type.setter
    def curve_type(self, value: AnimCurveType):
        self._flags &= ~self._FLAGS_MASK_CURVE_TYPE | value

    @property
    def pre_wrap(self) -> WrapMode:
        """The pre wrap mode, determining how to wrap the key data."""
        return WrapMode(self._flags >> 8 & 3)

    @pre_wrap.setter
    def pre_wrap(self, value: WrapMode):
        self._flags &= ~self._FLAGS_MASK_KEY_TYPE | value

    @property
    def post_wrap(self) -> WrapMode:
        """The post wrap mode, determining how to wrap the key data."""
        return WrapMode(self._flags >> 12 & 3)

    @post_wrap.setter
    def post_wrap(self, value: WrapMode):
        self._flags &= 53247 | value

    @property
    def elements_per_key(self) -> int:
        match (self.curve_type):
            case AnimCurveType.CUBIC:
                return 4
            case AnimCurveType.LINEAR:
                return 2
            case _:
                return 1

    def load(self, loader: core.ResFileLoader):
        frame_array_offs = 0
        key_array_offs = 0
        num_key = 0
        if (loader.is_switch):
            frame_array_offs = loader.read_offset()
            key_array_offs = loader.read_offset()
            self._flags = loader.read_uint16()
            num_key = loader.read_uint16()
            self.anim_data_offset = loader.read_uint32()
            self.start_frame = loader.read_single()
            self.end_frame = loader.read_single()
            self.scale = loader.read_single()
            self.offs = loader.read_single()
            self.delta = loader.read_single()
            padding = loader.read_int32()
        else:
            self._flags = loader.read_uint16()
            num_key = loader.read_uint16()
            self.anim_data_offset = loader.read_uint32()
            self.start_frame = loader.read_uint32()
            self.end_frame = loader.read_uint32()
            self.scale = loader.read_single()
            self.offs = loader.read_single()
            if loader.res_file.version >= 0x03040000:
                self.delta = loader.read_single()
            frame_array_offs = loader.read_offset()
            key_array_offs = loader.read_offset()

        def loadframes():
            match (self.frame_type):
                case AnimCurveFrameType.SINGLE:
                    return loader.read_singles(num_key)
                case AnimCurveFrameType.DECIMAL_10X5:
                    dec10x5frames: list[float] = [0.0] * num_key
                    for i in range(num_key):
                        dec10x5frames[i] = float(loader.read_decimal10x5())
                    return tuple(dec10x5frames)
                case AnimCurveFrameType.BYTE:
                    return loader.read_bytes(num_key)  # maybe
                case _:
                    raise TypeError(
                        f"Invalid FrameType {self.frame_type.name}")
        self.frames = loader.load_custom(tuple, loadframes, frame_array_offs)

        def loadkeys():
            elements_per_key = self.elements_per_key
            keys: list[tuple] = [
                tuple() * elements_per_key for i in range(num_key)]
            match (self.key_type):
                case AnimCurveKeyType.SINGLE:
                    for i in range(num_key):
                        if (self.curve_type is AnimCurveType.STEP_INT or
                                self.curve_type is AnimCurveType.STEP_BOOL):
                            keys[i] = loader.read_uint32s(elements_per_key)
                        else:
                            keys[i] = loader.read_singles(elements_per_key)
                case AnimCurveKeyType.INT16:
                    for i in range(num_key):
                        keys[i] = loader.read_int16s(elements_per_key)
                case AnimCurveKeyType.SBYTE:
                    for i in range(num_key):
                        keys[i] = loader.read_sbytes(elements_per_key)
                case _:
                    raise TypeError(f"Invalid KeyType {self.key_type.name}")
            return tuple(keys)  # only makes the outer list a tuple.
        self.keys = loader.load_custom(tuple, loadkeys, key_array_offs)

        if (self.curve_type is AnimCurveType.STEP_BOOL):
            key_idx = 0

            self.key_step_bool_data = [False] * num_key
            for i in range(len(self.keys)):
                if (num_key <= key_idx):
                    break

                value = self.keys[i][0]

                # Bit shift each key value
                for j in range(32):
                    if (num_key <= key_idx):
                        break

                    set_ = bool((value & 0x01) != 0)
                    value >>= 1

                    self.key_step_bool_data[key_idx] = set_
                    key_idx += 1


class AnimCurveFrameType(IntEnum):
    """Represents the possible data types in which AnimCurve.Frames are stored.
    For simple library use, they are always converted them to and from 
    Single instances.
    """
    # 16 bit
    SINGLE = 0
    """The frames are stored as Single instances."""

    DECIMAL_10X5 = 1
    """The frames are stored as Decimal10x5 instances."""

    BYTE = 2
    """The frames are stored as Byte instances."""


class AnimCurveKeyType(IntFlag):
    """Represents the possible data types in which AnimCurve.Keys are stored.
    For simple library use, they are always converted them to and from 
    Single instances.
    """
    # 16 bit
    SINGLE = 0 << 2
    """The keys are stored as Single instances."""

    INT16 = 1 << 2
    """The keys are stored as Decimal10x5 instances."""

    SBYTE = 2 << 2
    """The keys are stored as Signed Byte instances."""


class AnimCurveType(IntFlag):
    """Represents the type of key values stored by this curve. This also 
    determines the number of required elements to define a key in the 
    AnimCurve.Keys array. Use the AnimCurve.elements_per_key() method to 
    retrieve the number of elements required for the AnimCurve.curve_type
    of that curve.
    """
    CUBIC = 0 << 4
    """The curve uses cubic interpolation.
    4 elements of the AnimCurve.keys array form a key."""

    LINEAR = 1 << 4
    """The curve uses linear interpolation.
    2 elements of the AnimCurve.keys array form a key.
    """

    BAKED_FLOAT = 2 << 4
    """1 element of the AnimCurve.keys array forms a key."""

    STEP_INT = 4 << 4
    """1 element of the AnimCurve.keys array forms a key."""

    BAKED_INT = 5 << 4
    """1 element of the AnimCurve.keys array forms a key."""

    STEP_BOOL = 6 << 4
    """1 element of the AnimCurve.keys array forms a key."""

    BAKED_BOOL = 7 << 4
    """1 element of the AnimCurve.keys array forms a key."""


class WrapMode(IntEnum):
    CLAMP = 0
    REPEAT = 1
    MIRROR = 2


@dataclass
class Srt2D:
    """Represents a 2D transformation."""
    scaling: tuple[float, float]
    rotation: float
    translation: tuple[float, float]

    def __repr__(self):
        return f"Srt2D[{self.scaling} {self.rotation} {self.translation}]"

    def __bool__(self):
        return (
            self.scaling != (1.0, 1.0)
            or self.rotation != 0.0
            or self.translation != (0.0, 0.0)
        )


@dataclass
class Srt3D:
    """Represents a 3D transformation."""
    scaling: tuple[float, float, float]
    rotation: tuple[float, float, float]
    translation: tuple[float, float, float]

    def __repr__(self):
        return f"Srt3D[{self.scaling} {self.rotation} {self.translation}]"

    def __bool__(self):
        return (
            self.scaling != (1.0, 1.0, 1.0)
            or self.rotation != (0.0, 0.0, 0.0)
            or self.translation != (0.0, 0.0, 0.0)
        )

@dataclass
class TexSrt:
    """Represents a 2D texture transformation."""
    mode: TexSrtMode
    scaling: tuple[float, float]
    rotation: float
    translation: tuple[float, float]

    def __repr__(self):
        return f"TexSrt[{self.mode.name} {self.scaling} {self.rotation} {self.translation}]"

    def __bool__(self):
        return (
            self.scaling != (1.0, 1.0)
            or self.rotation != 0.0
            or self.translation != (0.0, 0.0)
        )

class TexSrtMode(IntEnum):
    MODE_MAYA = 0
    MODE_3DS_MAX = 1
    MODE_SOFTIMAGE = 2


class TextureRef(core.ResData):
    """Represents a reference to a Texture instance by name."""

    def __init__(self, name=""):
        self.texture: texture.TextureShared

        self.name = name

    def load(self, loader: core.ResFileLoader):
        name = loader.load_string()
        texture = loader.load(WiiU.Texture)


class Buffer(core.ResData):
    """Represents a buffer of data uploaded to the GX2 GPU which can hold 
    arbitrary data.
    """

    def __init__(self):
        self.stride: int
        self.data: list[bytes]
        self.flags: int
        self.buff_offs: int

    @property
    def size(self):
        return sum([len(x) for x in self.data])

    def load(self, loader: core.ResFileLoader):
        data_pointer = loader.read_uint32()
        size = loader.read_uint32()
        handle = loader.read_uint32()
        self.stride = loader.read_uint16()
        num_buffering = loader.read_uint16()
        context_pointer = loader.read_uint32()

        def __loaddata():
            data = []
            for i in range(num_buffering):
                data.append(loader.read_bytes(size))
            return tuple(data)
        data = loader.load_custom(tuple, lambda: __loaddata())


class ResString(core.ResData):
    """Represents a String which is stored in a ResFile"""

    def __init__(self, value=None, encoding: str = ''):
        if (value):
            if (isinstance(value, str)):
                self.encoding = encoding
                self.string = value
            elif (isinstance(value, ResString)):
                self.string = value.string
                self.encoding = value.encoding
        else:
            self.string: str
            self.encoding = None

    def __str__(self):
        return self.string

    def __repr__(self) -> str:
        return f'res\'{self.string}\''

    def load(self, loader: core.ResFileLoader):
        if (loader.is_switch):
            self.string = loader.load_string(self.encoding)
        else:
            self.string = loader.read_string(self.encoding)

    def save(self, saver):
        # TODO
        pass


class StringTable(core.ResData):
    def __init__(self):
        self.strings = []

    def load(self, loader: core.ResFileLoader):
        self.strings.clear()
        if (loader.is_switch):
            loader.seek(-0x14, io.SEEK_CUR)
            signature = loader.read_uint32()
            block_offs = loader.read_uint32()
            block_size = loader.read_uint64()
            num_strs = loader.read_uint32()

            for i in range(num_strs):
                size = loader.read_uint16()
                self.strings.append(loader.read_null_string())
                loader.align(2)


class UserData(core.ResData):
    """Represents custom user variables which can be attached to many sections
    and subfiles of a ResFile
    """

    def __init__(self):
        self._value: object
        self.type: UserDataType

        self.name = ""
        self.set_value([])

    def __repr__(self):
        return "UserData{" + str(self.name) + "}"

    def get_data(self):
        return self._value

    def set_value(self, value, as_unicode=False):
        if type(value) is bytes | bytearray:
            self.type = UserDataType.BYTE
            self._value = value
        elif len(value) == 0 or type(value[0]) is int:
            self.type = UserDataType.INT32
            self._value = value
        elif type(value[0]) is float:
            self.type = UserDataType.SINGLE
            self._value = value
        elif type(value[0]) is str:
            self.type = (UserDataType.WString
                         if as_unicode
                         else UserDataType.STRING)
            self._value = value
        else:
            raise TypeError(
                f"UserData recieved unsupported type {type(value).__name__}")

    # there would be a "Bytes" here but signed bytes and int32 just use "int"

    def load(self, loader: core.ResFileLoader):
        if (loader.is_switch):
            self.name = loader.load_string()
            data_offs = loader.read_offset()
            count = 0
            if (loader.res_file.version_major2 <= 2
                    and loader.res_file.version_major2 == 0):

                reserved = loader.read_raw_string(8)
                count = loader.read_uint32()
                self.type = UserDataType(loader.read_uint32())
            else:
                count = loader.read_uint32()
                self.type = UserDataType(loader.read_byte())
                reserved = loader.read_raw_string(43)

            match self.type:
                case UserDataType.BYTE:
                    self._value = loader.load_custom(
                        tuple, lambda: loader.read_sbytes(count), data_offs
                    )
                case UserDataType.INT32:
                    self._value = loader.load_custom(
                        tuple, lambda: loader.read_int32s(count), data_offs
                    )
                case UserDataType.SINGLE:
                    self._value = loader.load_custom(
                        tuple, lambda: loader.read_singles(count), data_offs
                    )
                case UserDataType.STRING:
                    self._value = loader.load_custom(
                        tuple, lambda: loader.load_strings(count, "utf-8"),
                        data_offs
                    )
                case UserDataType.WString:
                    self._value = loader.load_custom(
                        tuple, lambda: loader.load_strings(count, "utf-16"),
                        data_offs
                    )
        else:
            self.name = loader.load_string()
            count = loader.read_uint16()
            self.type = UserDataType(loader.read_byte())
            loader.seek(1)
            match self.type:
                case UserDataType.BYTE:
                    self._value = loader.read_bytes(count)
                case UserDataType.INT32:
                    self._value = loader.read_int32s(count)
                case UserDataType.SINGLE:
                    self._value = loader.read_singles(count)
                case UserDataType.STRING:
                    self._value = loader.load_strings(count, "utf-8")
                case UserDataType.WString:
                    self._value = loader.load_strings(count, "utf-16")


class UserDataType(IntEnum):
    """Represents the possible data types of values stored in UserData 
    instances.
    """
    INT32 = 0
    """The values are an Int32 array"""
    SINGLE = 1
    """The values are a Float array"""
    STRING = 2
    """The values are a string array encoded in ASCII"""
    WString = 3
    """The values are a string array encoded in UTF-16"""
    BYTE = 4
    """The values are a Byte array"""


class Node(Generic[T]):
    """Represents a node forming the Patricia trie of the dictionary."""
    size_in_bytes = 16

    def __init__(self, key=None, value=None):
        self.reference = 0xFFFFFFFF
        self.idx_left: int
        self.idx_right: int
        self.key: str
        self.value: T
        if (key):
            self.key = key
        if (value):
            self.value = value

    def __bool__(self):
        if (hasattr(self, 'key')):
            return True
        return False

    def __repr__(self) -> str:
        return f"ResDictNode('{self.key}': '{self.value}')"


class ResDict(core.ResData, Collection[Node[T]]):
    """Represents the non-generic base of a dictionary which can quickly
    look up ResData instances via key or index.
    """

    def __init__(self):
        self._nodes: list[Node[T]] = [Node('')]

    def __len__(self):
        return len(self._nodes) - 1

    def __iter__(self):
        return iter(self._nodes[1:])

    def __repr__(self):
        return (
            'ResDict{'
            + ', '.join([f'{key}: {value}'for key, value in self.items()])
            + '}'
        )

    def __contains__(self, x: object) -> bool:
        node, index = self.__lookup(x, False)
        if (node):
            return True
        else:
            return False

    # Operators

    @overload
    def __getitem__(self, key: int | str) -> T:
        ...

    @overload
    def __getitem__(self, key: type[core.ResData]) -> str:
        ...

    def __getitem__(self, key):
        if (isinstance(key, int | str)):
            node, index = self.__lookup(key)
            return node.value

        if (isinstance(key, core.ResData)):
            node, index = self.__lookup(key)
            return node.key

    def __setitem__(self, key, value: T):
        if (isinstance(key, int)):
            node, index = self.__lookup(key)
            node.value = value

        if (isinstance(key, str)):
            node, index = self.__lookup(key, False)
            if (node):
                node.value = value
            else:
                self._nodes.append(Node(key, value))

        if (isinstance(key, core.ResData)):
            self.__lookup(key)
            node, index = self.__lookup(value)
            if (node):
                raise ValueError(f"Key {value} already exists.")

    # Properties

    def keys(self) -> Iterator[str]:
        """Gets all keys under which instances are stored."""
        for node in self._nodes[1:]:
            yield node.key

    def values(self) -> Iterator[T]:
        """Gets all stored instances."""
        for node in self._nodes[1:]:
            yield node.value

    def items(self):
        for node in self._nodes[1:]:
            yield (node.key, node.value)

    # Public Methods

    def clear(self):
        """Removes all elements from the dictionary"""
        self._nodes.clear()
        self._nodes.append(Node(key=''))

    def contains_key(self, key):
        """Determines whether an instance is saved
        under the given key in the dictionary.
        """
        node, index = self.__lookup(key, False)
        if (node):
            return True
        return False

    def get_key(self, index: int):
        """Returns they key of a given index"""
        node, idx = self.__lookup(index, True)  # XXX Shouldn't this be false?
        if (node):
            return node.key
        return ""

    def key_index(self, key: str):
        """Searches for the specified key and returns the zero-based
        index of the first occurrence within the entire dictionary.
        """
        node, index = self.__lookup(key, False)
        return (index if node else -1)

    def rename(self, key, new_key):
        """Changes the key of the instance currently saved under the
        given key to the new_key
        """
        # Throw if key doesnt exist
        node, index = self.__lookup(key)
        # Throw if new key already exists
        existingnode, index = self.__lookup(key, False)
        if (existingnode):
            raise ValueError(f'Key "{new_key}" already exists.')

    def remove_key(self, key):
        """Removes the first occurrence of the instance with the
        specific key from the dictionary.
        """
        node, index = self.__lookup(key, False)
        if (node):
            self._nodes.remove(node)
            return True
        else:
            return False

    def remove_at(self, index):
        """Removes the instance at the specified index of the dictionary."""
        node, idx = self.__lookup(index, True)
        self._nodes.remove(node)

    def try_get_value(self, key):
        node, index = self.__lookup(key, False)
        if (node):
            return node.value
        else:
            return None

    # Internal Methods

    def append(self, key, value):
        """Adds the given value under the specified key."""
        node, index = self.__lookup(key, False)
        if (node):
            raise ValueError(f'Key "{key}" already exists.')
        self._nodes.append(Node(key, value))

    def value_index(self, value: core.ResData):
        """Searches for the specified value and returns the zero-based
        index of the first occurrence within the entire dictionary."""
        node, index = self.__lookup(value, False)
        if (node):
            return index
        else:
            return -1

    def remove(self, value: core.ResData):
        """Removes the first occurrence of a specific value
        from the dictionary."""
        node, index = self.__lookup(value, False)
        if (node):
            self._nodes.remove(node)
            return True
        else:
            return False

    def to_dict(self) -> dict[str, T]:
        """Copies the elements of the dictionary to a python dict
        """
        res_data = {}
        for i, node in enumerate(self):
            res_data[node.key] = node.value
        return res_data

    def try_get_key(self, value):
        """Returns True if a key was found for the given value and has been
        assigned to key, or None if no key was found.
        """
        node, index = self.__lookup(value, False)
        if (node):
            return node.key
        else:
            return None

    # Methods

    def load(self, T: type[core.ResData], loader: core.ResFileLoader):
        loader.read_uint32()  # Always 0 on switch, total size on Wii U
        num_nodes = loader.read_uint32()  # Excluding Root node

        i = 0
        # Read the nodes including the root node.
        nodes = []
        while (num_nodes >= 0):
            nodes.append(self.__read_node(T, loader))
            i += 1  # XXX What does i do here?
            num_nodes -= 1
        self._nodes = nodes

    # Protected Methods

    def _load_node_value(self, T, loader):
        """Loads an ResData instance from the given loader"""
        return loader.load(T)

    # Private Methods

    def __read_node(self, T, loader: core.ResFileLoader) -> Node:
        node = Node()

        node.reference = loader.read_uint32()
        node.idx_left = loader.read_uint16()
        node.idx_right = loader.read_uint16()
        node.key = loader.load_string()
        if (not loader.is_switch):
            node.value = self._load_node_value(T, loader)
        return node

    @singledispatchmethod
    def __lookup(self, value, throwonfail=True):
        for i, found_node in enumerate(self):
            if (found_node.value == value):
                return (found_node, i)
        if (throwonfail):
            raise ValueError("{key} not found in {this}.")
        return (Node(), -1)

    @__lookup.register
    def _(self, value: ResString, throwonfail=True):
        for i, found_node in enumerate(self):
            if (isinstance(found_node.value, ResString)):
                if (str(found_node.value) == str(value)):
                    return (found_node, i)
        return (Node(), -1)

    @__lookup.register
    def _(self, key: int, throwonfail=True):
        if (key < 0 or key > len(self._nodes)):
            if (throwonfail):
                raise IndexError(f"{key} out of bounds in {self}.")
            return (Node(), -1)
        node = self._nodes[key + 1]
        return (node, key)

    @__lookup.register
    def _(self, key: str, throwonfail=True):
        for i, found_node in enumerate(self):
            if (found_node.key == key):
                return (found_node, i)
        if (throwonfail):
            raise ValueError("{key} not found in {this}.")
        return (Node(), -1)

