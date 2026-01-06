from .core import ResData, ResFileLoader


class RelocationTable(ResData):
    _SIGNATURE = "_RLT"

    def __init__(self):
        self.this_table_offs: int
        self.section_count: int

    def load(self, loader: ResFileLoader):
        loader._check_signature(self._SIGNATURE)
        self.this_table_offs = loader.read_uint32()
        self.section_count = loader.read_uint32()
        self.reserved = loader.read_uint32()

        self.reloc_dict = {}
        sections = []
        for i in range(self.section_count):
            sections.append(loader.load(self.ResSection, False))
        for section in sections:
            file_base = (0 if section.base_pointer == 0
                         else section.base_pointer - section.region_offs)
            for e in range(section.entry_count):
                entry = loader.load(self.ResEntry, False)
                region_offs = entry.region_offs
                offset_count = entry.reloc_count
                offset_mask = offset_count & 3
                for array_idx in range(entry.array_count):
                    region_offset_iter = region_offs
                    for offset_idx in range(offset_count):
                        reloc_pointer = (file_base + region_offset_iter
                                         if region_offset_iter != 0
                                         else 0)
                        self.reloc_dict[region_offset_iter] = reloc_pointer
                        region_offset_iter += 8
                    region_offs = (region_offs
                                   + offset_count * 8
                                   + entry.array_stride * 8)

    @staticmethod
    def calc_table_size(sections, entries):
        return sections * 0x18 + entries * 0x8 + 0x10

    def get_base_entry_offs(self, idx):
        return (self.this_table_offs + 0x10
                + 0x18 * self.section_count
                + idx * 0x8)

    def get_section(self, section_idx):
        return self.this_table_offs + 0x10 + section_idx * 0x18

    class ResSection(ResData):
        def __init__(self):
            self.base_pointer: int
            self.region_offs: int
            self.region_size: int
            self.base_entry_idx: int
            self.entry_count: int
            self.entries: list

        def load(self, loader: ResFileLoader):
            self.base_pointer = loader.read_uint64()
            self.region_offs = loader.read_uint32()
            self.region_size = loader.read_uint32()
            self.base_entry_idx = loader.read_uint32()
            self.entry_count = loader.read_uint32()

    class ResEntry(ResData):
        def __init__(self):
            self.region_offs: int
            self.array_count: int
            self.reloc_count: int
            self.array_stride: int

        def load(self, loader: ResFileLoader):
            self.region_offs = loader.read_uint32()
            self.array_count = loader.read_uint16()
            self.reloc_count = loader.read_byte()
            self.array_stride = loader.read_byte()
