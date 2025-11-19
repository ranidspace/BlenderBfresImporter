# Bfres Importer

This is a Blender(3.6+) addon imports the Nintendo .bfres file format.

## Installation

Download the zip from the Releases section of the page, and in Blender, open preferences, Get Extensions, and on the dropdown menu at the top right, click "Install from disk" and select the zip file.

## Notes

This addon is not fully featured yet, and there's a lot to fix and change. The backend for this addon, [bfrespy](https://github.com/ranidspace/bfrespy), is currently incomplete.

Wii U files are currently unable to be imported, and a few things, notably skeletal animations are not in the Importer.

## Tips

### Material Data

This addon imports the material parameters, shader options and render info of the bfres material into the "Custom Properties" of the Blender material.

The name of the parameter is prefixed with "MP_", "SO_" and "RI_" respectively. These can be used in a shader node setup, using the Attribute node, set to Object, and the Name as `materials[0]["name_of_param"]`

### Animation data

Animations are not fully supported, but importing the base animation data will import the first frame of the animations.

These animations are stored as Blender Actions, you can select an armature, and in the Armature Data panel, or animation editor, you can select the action. It may be useful for some quick poses.

## References

This addon was originally a fork of [RenaKunisaki/bfres_importer](https://github.com/RenaKunisaki/bfres_importer)

- [Syroot/io_scene_bfres](https://gitlab.com/Syroot/NintenTools/io_scene_bfres)
- [KillzXGaming/SwitchToolbox](https://github.com/KillzXGaming/Switch-Toolbox)
- [KillzXGaming/BfresLibrary](https://github.com/KillzXGaming/BfresLibrary/)
- [python-pillow/Pillow](https://github.com/python-pillow/Pillow) (For BC6/BC7 Importing)
