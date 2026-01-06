import io
from .. import core, ResFile, common


class ResFileSwitchLoader(core.ResFileLoader):
    def __init__(self, res_file: ResFile,
                 stream: io.BytesIO | io.BufferedReader,
                 leave_open=False,
                 res_data: core.ResData | None = None):
        super().__init__(res_file, stream, leave_open, res_data)
        self.endianness = '<'
        self.is_switch = True

    def read_offset(self):
        """Reads a BFRES offset which is relative to itself,
        and returns the absolute address
        """
        offset = self.read_uint64()
        return 0 if offset == 0 else offset

    def readsize(self):
        return self.read_uint64()

    def load_header_block(self):
        offset = self.read_uint32()
        size = self.read_uint64()

    def load_string(self, encoding=None) -> str:
        offset = self.read_offset()
        if (offset == 0):
            return ''
        if (offset in common.stringcache):
            return common.stringcache[offset]
        if (offset < 0):
            return ''
        with self.temporary_seek(offset, io.SEEK_SET) as reader:
            try:
                return self.read_string(encoding)
            except IndexError:
                return ''

    def load_strings(self, count, encoding=None) -> tuple[str, ...]:
        offsets = self.read_uint64s(count)
        names = []
        with self.temporary_seek():
            for i, offset in enumerate(offsets):
                if (offset == 0):
                    names.append(None)
                if (offset in common.stringcache):
                    names[i] = common.stringcache[offset]
                else:
                    self.seek(offset, io.SEEK_SET)
                    names.append(self.read_string(encoding))
        return tuple(names)

    def read_string(self, encoding=None):
        size = self.read_uint16()
        return self.read_null_string(encoding)
