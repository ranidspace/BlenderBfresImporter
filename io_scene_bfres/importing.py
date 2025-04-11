import io
import logging
import struct
from pathlib import Path

import bpy
import zstandard

from . import bfrespy, yaz0
from .bone_anim_importer import BoneAnimationImporter
from .exceptions import MalformedFileError, UnsupportedFileTypeError
from .model_importer import ModelImporter

log = logging.getLogger(__name__)


class Importer:
    def __init__(self, operator, context, filepath):
        self.operator = operator
        self.context = context
        self.bfres: bfrespy.ResFile

        # Extract path information.
        self.filepath = Path(filepath)
        self.directory = self.filepath.parent
        self.filename = self.filepath.name
        self.fileext = self.filepath.suffix.upper()
        # Create work directories for temporary files.

    def run(self):
        with open(self.filepath, "rb") as f:
            return self._load_stream(f)

    def _load_stream(self, raw) -> set:
        """Check if the stream is decompressed, and then check if it's an archive"""
        # Ensure to have a stream with decompressed data.
        magic = raw.read(4)
        raw.seek(0, io.SEEK_SET)
        match magic:
            # Uncompressed
            case b"FRES":
                return self._import_bfres(raw)
            case b"BNTX":
                return self._import_bntx(raw)
            # Archive
            case b"SARC":
                r = self._get_from_sarc(raw)
                return self._load_stream(r)
            # Compressed
            case b"\x28\xb5\x2f\xfd":  # zstd
                dctx = zstandard.ZstdDecompressor()
                r = dctx.decompress(raw.read())
                return self._load_stream(io.BytesIO(r))
            case b"Yaz0":
                r = yaz0.decompress(raw)
                return self._load_stream(r)
            case _:
                raise UnsupportedFileTypeError(magic)

    def _import_bfres(self, stream):
        """Import a BFRES file, and return 'FINISHED' if it succeeds"""
        bfres = bfrespy.ResFile(stream)
        self.bfres = bfres
        # Read and import any external files
        for node in bfres.external_files:
            self._import_embed(node, bfres.name)

        if self.operator.import_anims:
            anim_imp = BoneAnimationImporter(self)
            anim_imp._import_animations(bfres)

        # If there's more than one model, add them all to a collection.
        if len(bfres.models) > 1:
            collection = bpy.data.collections.new(name=bfres.name)
            bpy.context.scene.collection.children.link(collection)
        else:
            collection = bpy.context.scene.collection

        model_imp = ModelImporter(self)
        for fmdl in bfres.models.values():
            model_imp._convert_fmdl(fmdl, collection)

        return {"FINISHED"}

    def _import_bntx(self, stream):
        """Import a BFRES file, and return 'FINISHED' if it succeeds"""
        from . import bntx

        bntx_ = bntx.BNTX(stream)

        from .texture_importer import TextureImporter

        tex_imp = TextureImporter(self)
        self.texture_map = tex_imp.import_textures(bntx_)

        return {"FINISHED"}

    def _import_embed(self, node, name):
        """Import an embedded file in the ResFile"""
        name = node.key
        file = node.value
        if name.endswith(".txt"):
            # embed text blend file
            obj = bpy.data.texts.new(name=name)
            obj.write(file.data.decode("utf-8"))
        else:
            if file.data:
                try:
                    self._load_stream(io.BytesIO(file.data))
                except UnsupportedFileTypeError as ex:
                    log.debug("Embedded file '%s' is of unsupported type '%s'", name, ex.magic)
            else:
                log.debug("Embedded file '%s' is empty", name)

    @staticmethod
    def _get_from_sarc(raw: io.BytesIO | io.BufferedReader):
        """Attempt to return a FRES file from a SARC archive."""
        log.debug("Extracting from SARC")
        raw.seek(6, io.SEEK_CUR)
        bom = raw.read(2)
        endianness = ">" if bom == 0xFEFF else "<"
        raw.seek(4, io.SEEK_CUR)
        offs = struct.unpack(endianness + "I", raw.read(4))[0]
        raw.seek(10, io.SEEK_CUR)
        num_nodes = struct.unpack(endianness + "H", raw.read(2))[0]
        raw.seek(4, io.SEEK_CUR)
        files = []
        for _ in range(num_nodes):
            raw.seek(8, io.SEEK_CUR)
            start_offs = struct.unpack(endianness + "I", raw.read(4))[0]
            end_offs = struct.unpack(endianness + "I", raw.read(4))[0]
            files.append((start_offs, end_offs))
        for fileoff in files:
            raw.seek(fileoff[0] + offs, io.SEEK_SET)
            if raw.read(4) == b"FRES":
                raw.seek(-4, io.SEEK_CUR)
                return io.BytesIO(raw.read(fileoff[1] - offs))
        raise MalformedFileError("Embedded SARC file does not contain FRES")

    @staticmethod
    def _add_object_to_collecton(obj, collection_name):
        """Add an object to a collection, and create it if it does not already exist."""
        group = bpy.data.collections.get(collection_name, bpy.data.collections.new(name=collection_name))

        # Link the provided object to it.
        if obj.name not in group.objects:
            group.objects.link(obj)
