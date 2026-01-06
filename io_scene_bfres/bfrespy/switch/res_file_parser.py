from __future__ import annotations
import io
from .switchcore import ResFileSwitchLoader
from .memory_pool import MemoryPool, BufferInfo
from .. import common, models, skeletal_anim
from .. import res_file as res
from .. import external_file as ext


class ResFileParser:
    @staticmethod
    def load(loader: ResFileSwitchLoader, res_file: res.ResFile):
        # File Header
        loader._check_signature("FRES")
        padding = loader.read_uint32()
        res_file.version = loader.read_uint32()
        res_file.set_version_info(res_file.version)
        res_file.endianness = loader._read_byte_order()
        res_file.alignment = loader.read_byte()
        # Thanks MasterF0X for pointing out the layout of the these
        res_file.target_addr_size = loader.read_byte()
        offset_to_filename = loader.read_uint32()
        res_file.flags = loader.read_uint16()
        res_file.block_offs = loader.read_uint16()
        relocation_table_offs = loader.read_uint32()
        siz_file = loader.read_uint32()

        # loader.load_relocation_table(relocation_table_offs)

        # Bfres Header
        res_file.name = loader.load_string()
        model_offs = loader.read_offset()
        model_dict_offs = loader.read_offset()
        if (loader.res_file.version_major2 >= 9):
            loader.read_bytes(32)  # reserved

        res_file.skeletal_anims = loader.load_dict_values(
            skeletal_anim.SkeletonAnim)
        # TODO Read These properly
        res_file.material_anims = loader.read_offset()
        res_file.material_anims = loader.read_offset()
        res_file.bone_visibility_anims = loader.read_offset()
        res_file.bone_visibility_anims = loader.read_offset()
        res_file.shape_anims = loader.read_offset()
        res_file.shape_anims = loader.read_offset()
        res_file.scene_anims = loader.read_offset()
        res_file.scene_anims = loader.read_offset()

        res_file.mempool = loader.load(MemoryPool)
        res_file.buffer_info = loader.load(BufferInfo)

        if (loader.res_file.version_major2 >= 10):
            # Peek at external flags
            def peek_flags():
                with (loader.temporary_seek(0xee, io.SEEK_SET)):
                    return loader.read_byte()

            flags = peek_flags()
            if (res_file.has_flag(
                    flags, res_file.ExternalFlags.HOLDS_EXTERNAL_STRINGS)):
                externalFileOffset = loader.read_offset()
                externalFileDict = loader.load_dict(common.ResString)

                with (loader.temporary_seek(externalFileOffset, io.SEEK_SET)):
                    common.stringcache.clear()
                    for string in externalFileDict.keys():
                        string_id = loader.read_int64()
                        common.stringcache[string_id] = string
                return

            # GPU section for TOTK
            if (res_file.has_flag(flags,
                                  res_file.ExternalFlags.HAS_EXTERNAL_GPU)):
                with (loader.temporary_seek(siz_file, io.SEEK_SET)):
                    gpuDataOffset = loader.read_uint32()
                    gpuBufferSize = loader.read_uint32()

                    res_file.buffer_info = BufferInfo()
                    res_file.buffer_info.buff_offs = siz_file + 288

        res_file.external_files = loader.load_dict_values(ext.ExternalFile)
        padding1 = loader.read_uint64()
        res_file.string_table = loader.load(common.StringTable)
        string_pool_size = loader.read_uint32()
        num_model = loader.read_uint16()

        # Read models after buffer data
        res_file.models = loader.load_dict_values(
            models.Model, model_dict_offs, model_offs)

        if (loader.res_file.version_major2 >= 9):
            # Count for 2 new sections
            unkCount = loader.read_uint16()
            unk2Count = loader.read_uint16()

            if (unkCount != 0):
                raise ValueError("unk1 has section!")
            if (unk2Count != 0):
                raise ValueError("unk2 has section!")

        num_skeletal_anim = loader.read_uint16()
        num_material_anim = loader.read_uint16()
        num_bone_visibility_anim = loader.read_uint16()
        num_shape_anim = loader.read_uint16()
        num_scene_anim = loader.read_uint16()
        num_external_file = loader.read_uint16()
        res_file.external_flag = res.ResFile.ExternalFlags(
            loader.read_byte())
        reserve10 = loader.read_byte()

        padding3 = loader.read_uint32()

        if (reserve10 == 1 or res_file.external_flag != 0):
            res_file.data_alignment_override = 0x1000

        # TODO External Files and material animations
        """res_file.textures = ResDict()
        for ext in res_file.external_files:
            if (".bntx" in ext.key):
                bntx = BntxFile(io.BytesIO(ext.value.data))
                ext.Value.LoadedFileData = bntx
                for tex in bntx.nx.textures:
                    res_file.textures.append(
                        tex.Name, SwitchTexture(bntx, tex))

        res_file.tex_pattern_anims = ResDict(MaterialAnim)
        res_file.mat_visibility_anims = ResDict(MaterialAnim)
        res_file.shaderparam_anims = ResDict(MaterialAnim)
        res_file.color_anims = ResDict(MaterialAnim)
        res_file.tex_srt_anims = ResDict(MaterialAnim)

        # Split material animations into shader, texture, and visual animation lists
        for anim in res_file.material_anims.values:
            if (anim.name.contains("_ftp")):
                res_file.tex_pattern_anims.append(anim.name, anim)
            elif (anim.name.contains("_fts")):
                res_file.shaderparam_anims.append(anim.name, anim)
            elif (anim.name.contains("_fcl")):
                res_file.color_anims.append(anim.name, anim)
            elif (anim.name.contains("_fst")):
                res_file.tex_srt_anims.append(anim.name, anim)
            elif (anim.name.contains("_fvt")):
                res_file.mat_visibility_anims.append(anim.name, anim)
            elif (anim.material_anim_data_list != None and anim.material_anim_data_list.any(x= > x.visibily_count > 0)):
                res_file.mat_visibility_anims.append(anim.name, anim)
            elif (anim.material_anim_data_list != None and anim.material_anim_data_list.any(x= > x.texture_pattern_count > 0)):
                res_file.tex_pattern_anims.append(anim.name, anim)
            else:
                res_file.shaderparam_anims.append(anim.name, anim)"""
