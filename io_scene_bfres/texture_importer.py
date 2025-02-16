import numpy as np
import os.path
import os
import bpy
import logging
log = logging.getLogger(__name__)


class TextureImporter:
    """Imports texture images from BNTX archive."""

    def __init__(self, parent):
        self.parent = parent
        self.operator = parent.operator
        self.context = parent.context
        preferences = self.context.preferences

    def import_textures(self, bntx):
        """Import textures from BNTX."""
        images = {}
        for i, tex in enumerate(bntx.nx.textures):
            log.info("Importing texture %3d/%3d '%s' (%s)...",
                     i + 1, len(bntx.nx.textures), tex.name,
                     type(tex.format_).__name__)
            alpha = False
            isdata = True
            float_buffer = False
            if (b'\x05' in tex.channel_types):
                alpha = True
            if (tex.fmt_dtype.name == 'SRGB'):
                isdata = False
            if tex.fmt_dtype.name in ['UHALF', 'SINGLE']:
                isdata = False
                float_buffer = True

            image = bpy.data.images.new(
                name=self.operator.name_prefix+tex.name, width=tex.width,
                height=tex.height, float_buffer=float_buffer, alpha=alpha,
                is_data=isdata
            )

            # Issues arise when textures are not multiples of 4, pretty rare.
            if len(tex.pixels) > tex.width * tex.height * 4:
                pixels = tex.pixels[:tex.width * tex.height * 4]
                pixels = tex.format_.decodepixels(pixels)
            else:
                pixels = tex.format_.decodepixels(tex.pixels)

            if (self.operator.component_selector):
                temppix = pixels.copy()
                for ch in range(4):
                    if (tex.channel_types[ch] == ch + 2):
                        continue
                    match tex.channel_types[ch]:
                        case 0:
                            pixels[ch::4] = 0
                        case 1:
                            pixels[ch::4] = 1
                        case 2:
                            pixels[ch::4] = temppix[0::4]
                        case 3:
                            pixels[ch::4] = temppix[1::4]
                        case 4:
                            pixels[ch::4] = temppix[2::4]
                        case 5:
                            pixels[ch::4] = temppix[3::4]

            # Add some file data if it's needed:
            if tex.fmt_dtype.name in ['UHALF', 'SINGLE']:
                image.file_format = 'OPEN_EXR'
                image.colorspace_settings.name = 'sRGB'
            else:
                image.file_format = 'PNG'

            # flip image from dx to gl
            pixels = np.flipud(pixels.reshape((tex.height, tex.width, 4)))

            image.pixels = np.ravel(pixels)

            # save to file
            if (self.operator.dump_textures):
                if hasattr(self.parent, 'bfres'):
                    dir = bpy.utils.extension_path_user(__package__, path=self.parent.bfres.name, create=True)
                else:
                    dir = bpy.utils.extension_path_user(__package__, path='bntx', create=True)

                if image.file_format == 'OPEN_EXR':
                    image.filepath_raw = "%s/%s.exr" % (
                        dir, tex.name)
                else:
                    image.filepath_raw = "%s/%s.png" % (
                        dir, tex.name)
                log.info("Saving image to %s", image.filepath_raw)
                image.save()

            if self.parent.operator.add_fake_user:
                image.use_fake_user = True
            image.update()
            image.pack()
            images[tex.name] = image
        return images
