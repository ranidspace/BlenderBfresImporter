import io
import os
import bpy
import logging
import zstandard
import struct
from . import yaz0, bfrespy
from .model_importer import ModelImporter
from .bone_anim_importer import BoneAnimationImporter
from .exceptions import UnsupportedFileTypeError, MalformedFileError

log = logging.getLogger(__name__)
FILE_BUFFER_SIZE = 1024 * 1024

def open_bfres(filename, access="rb"):
    """Opens a bfres file for reading or writing,
    based on the way blender opens blend files.
    """

    def get_fres_from_sarc(raw):
        """Attempt to return a FRES file from a SARC archive."""
        raw.seek(6, io.SEEK_CUR)
        bom = raw.read(2)
        if (bom == 0xFEFF):
            endianness = '>'
        else:
            endianness = '<'
        raw.seek(4, io.SEEK_CUR)
        offs = struct.unpack(endianness + 'I', raw.read(4))[0]
        raw.seek(10, io.SEEK_CUR)
        num_nodes = struct.unpack(endianness + 'H', raw.read(2))[0]
        raw.seek(4, io.SEEK_CUR)
        files = []
        for i in range(num_nodes):
            raw.seek(8, io.SEEK_CUR)
            start_offs = struct.unpack(endianness + 'I', raw.read(4))[0]
            end_offs = struct.unpack(endianness + 'I', raw.read(4))[0]
            files.append(((start_offs, end_offs)))
        for fileoff in files:
            raw.seek(fileoff[0] + offs, io.SEEK_SET)
            if (raw.read(4) == b'FRES'):
                raw.seek(-4, io.SEEK_CUR)
                return io.BytesIO(raw.read(fileoff[1] - offs))
        raise MalformedFileError("Embedded SARC file does not contain FRES")



    fh = open(filename, access)
    magic = fh.read(4)
    fh.seek(0, os.SEEK_SET)

    if magic == "FRES":
        log.debug("Uncompressed BFRES file")
        return fh
    elif magic == b'\x28\xb5\x2f\xfd':
        log.debug("ZSTD Compressed BFRES file")
        fh.close()
        dctx = zstandard.ZstdDecompressor()
        with zstandard.open(filename, "rb") as fs:
            data = fs.read()
            if data[:4] == b"FRES":
                raw = io.BytesIO(data)
                return raw
    elif magic == b"Yaz0":
        log.debug("Yaz0 Compressed BFRES file")
        decompressed = yaz0.decompress(fh)
        fh.close()
        magic = decompressed.read(4)
        decompressed.seek(0, os.SEEK_SET)
        if magic == b"SARC":
            return get_fres_from_sarc(decompressed)
        else:
            return fh
    elif magic == b"SARC":
        log.debug("SARC archive")
        return get_fres_from_sarc(fh)
    else:
        raise UnsupportedFileTypeError(magic)

class Importer:
    def __init__(self, operator, context, filepath):
        self.operator = operator
        self.context = context
        self.bfres: bfrespy.ResFile

        # Extract path information.
        self.filepath = filepath
        self.directory = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.fileext = os.path.splitext(self.filename)[1].upper()
        # Create work directories for temporary files.

    def run(self):
        return self._import_bfres(self.filepath)

    def _import_bfres(self, filepath: str):
        """Import a BFRES file, and return 'FINISHED' if it succeeds"""
        with open_bfres(filepath) as fh:
            bfres = bfrespy.ResFile(fh)
        self.bfres = bfres
        # Read and import any external files
        for node in bfres.external_files:
            self._import_embed(node, bfres.name)

        if (self.operator.import_anims):
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

        return {'FINISHED'}

    def _import_bntx(self, stream):
        """Import a BFRES file, and return 'FINISHED' if it succeeds"""
        from . import bntx
        bntx_ = bntx.BNTX(stream)

        from .texture_importer import TextureImporter
        tex_imp = TextureImporter(self)
        self.texture_map = tex_imp.import_textures(bntx_)

        return {'FINISHED'}

    def _import_embed(self, node, name):
        """Import an embedded file in the ResFile"""
        name = node.key
        file = node.value
        if (name.endswith('.txt')):
            # embed text blend file
            obj = bpy.data.texts.new(name=name)
            obj.write(file.data.decode('utf-8'))
        else:
            if (file.data and file.data[:4] == b"BNTX"):
                self._import_bntx(io.BytesIO(file.data))
            else:
                log.debug("Unsupported file '%s'",
                          name)

    @staticmethod
    def _add_object_to_collecton(object, collection_name):
        """Add an object to a collection, and create it if it does not already exist."""
        group = bpy.data.collections.get(collection_name, bpy.data.collections.new(name=collection_name))

        # Link the provided object to it.
        if (object.name not in group.objects):
            group.objects.link(object)
