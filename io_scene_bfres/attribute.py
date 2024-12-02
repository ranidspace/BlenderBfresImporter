from enum import IntFlag


class AttributeFormat:
    def __init__(self, value: int):
        read = self.__read_format[value & 0x00FF]
        self.flags = self.AttribType(value & 0xFF00)
        if (type(read) is tuple):
            self.read: str = read[0]
            self.func = read[1]
            self.min = None
            self.max = None
        else:
            self.read: str = read
            self.func = None
            if (self.AttribType.SIGNED in self.flags):
                self.read = self.read.lower()
            self.min = self.__type_ranges[self.read[-1]][0]
            self.max = self.__type_ranges[self.read[-1]][1]

    @staticmethod
    def unpack10bit(val):
        if (type(val) in (list, tuple)):
            val = val[0]  # grumble grumble struct is butts
        res = []
        for i in range(3):
            s = (val >> (i * 10)) & 0x200
            v = (val >> (i * 10)) & 0x1FF
            if (s):
                v = v - 512
            if (v < -511):
                v = -511
            res.append(v / 511)
        res.append(val >> (30))
        return tuple(res)

    @staticmethod
    def unpack_arm_half_float(val):
        """Unpack 16-bit half-precision float.

        Uses ARM alternate format which does not encode Inf/NaN.
        """
        if (type(val) in (list, tuple)):
            return tuple(map(AttributeFormat.unpack_arm_half_float, val))
        frac = (val & 0x3FF) / 0x3FF
        exp = (val >> 10) & 0x1F
        sign = -1 if (val & 0x8000) else 1
        if (exp == 0):
            return sign * (2 ** -14) * frac
        else:
            return sign * (2 ** (exp - 15)) * (1 + frac)

    class AttribType(IntFlag):
        INTEGER = 0x100
        SIGNED = 0x200
        DEGAMMA = 0x400
        SCALED = 0x800

    __type_ranges = {  # name: (min, max)
        'b': (-0x80, 0x7F),
        'B': (0, 0xFF),
        'h': (-0x8000, 0x7FFF),
        'H': (0, 0xFFFF),
        'i': (-0x80000000, 0x7FFFFFFF),
        'I': (0, 0xFFFFFFFF),
        'f': (None, None),
    }

    __read_format = {
        0x00: 'B',
        0x01: ('B', 'nibble'),
        0x02: 'H',
        0x03: ('H', unpack_arm_half_float),
        0x04: '2B',
        0x05: 'I',
        0x06: 'f',
        0x07: '2H',
        0x08: ('2H', unpack_arm_half_float),
        0x09: ('I', 'test'),
        0x0A: '4B',
        0x0B: ('I', unpack10bit),
        0x0C: '2I',
        0x0D: '2f',
        0x0E: '4H',
        0x0F: ('4H', unpack_arm_half_float),
        0x10: '3I',
        0x11: '3f',
        0x12: '4I',
        0x13: '4f'
    }
