#!/usr/bin/env python3
# type: ignore[reportInvalidTypeForm]
"""BFRES importer/decoder for Blender.

This script can also run from the command line without Blender,
in which case it just prints useful information about the BFRES.
"""

import logging

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
from bpy_extras.io_utils import ImportHelper

log = logging.getLogger(__name__)


class ImportBFRES(bpy.types.Operator, ImportHelper):
    """Load a BFRES model file"""

    bl_idname = "import_scene.bfres"
    bl_label = "Import NX BFRES"
    bl_options = {"UNDO"}

    filename_ext = ".bfres"

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    filter_glob: StringProperty(
        default="*.sbfres;*.bfres;*.fres;*.szs;*.zs",
        options={"HIDDEN"},
    )

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    ui_tab: EnumProperty(
        items=(("MAIN", "Main", "Main basic settings"),),
        name="ui_tab",
        description="Import options categories",
    )

    import_tex_file: BoolProperty(
        name="Import .Tex File",
        description="Import textures from a .Tex file with same name, if it exists.",
        default=True,
    )

    component_selector: BoolProperty(
        name="Use Component Selector",
        description="Uses the component selector for each texture. Turn it on if the colours look off",
        default=False,
    )

    dump_textures: BoolProperty(
        name="Dump Textures",
        description="Export textures to PNG.",
        default=False,
    )

    custom_normals: BoolProperty(
        name="Custom Normals",
        description="Uses the n0 attribute of the model to compute the normals.",
        default=True,
    )

    lod_index: IntProperty(
        name="LOD index",
        description="The index of the LOD to import. Lower is more detail.",
        default=0,
        min=0,
        max=255,
    )

    name_prefix: StringProperty(
        name="Material/Texture Name Prefix",
        description="Text to prepend to material and texture names to keep them unique.",
        maxlen=32,
        default="",
    )

    add_fake_user: BoolProperty(
        name="Add Fake User",
        description="Adds a fake user to images and actions to prevent them from being deleted on save.",
        default=False,
    )

    import_anims: BoolProperty(
        name="Import base animation data",
        description="Imports data and the first frame of the animations as actions.",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        import_panel_textures(layout, self)
        import_panel_mesh(layout, self)
        import_panel_material(layout, self)
        import_panel_misc(layout, self)

    def execute(self, context):
        import os

        ret = {"CANCELLED"}

        if self.files:
            dirname = os.path.dirname(self.filepath)
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if self.unit_import(path) == {"FINISHED"}:
                    ret = {"FINISHED"}
            return ret
        return self.unit_import(self.filepath)

    def unit_import(self, path):
        import os

        from .importing import Importer

        if self.import_tex_file:
            texpath, ext = os.path.splitext(self.filepath)
            texpath = texpath + ".Tex" + ext
            if os.path.exists(texpath):
                log.info("Importing linked file: %s", texpath)
                importer = Importer(self, path)
                importer.run()

        log.info("importing: %s", path)
        importer = Importer(self, path)
        return importer.run()


def import_panel_textures(layout, operator):
    header, body = layout.panel("BFRES_import_texture", default_closed=False)
    header.label(text="Textures")
    if body:
        body.prop(operator, "import_tex_file")
        body.prop(operator, "dump_textures")
        body.prop(operator, "component_selector")


def import_panel_mesh(layout, operator):
    header, body = layout.panel("BFRES_import_mesh", default_closed=False)
    header.label(text="Meshes")
    if body:
        body.prop(operator, "custom_normals")
        body.prop(operator, "lod_index")


def import_panel_material(layout, operator):
    header, body = layout.panel("BFRES_import_mat", default_closed=False)
    header.label(text="Materials")
    if body:
        body.prop(operator, "name_prefix")


def import_panel_misc(layout, operator):
    header, body = layout.panel("BFRES_import_misc", default_closed=False)
    header.label(text="Misc")
    if body:
        body.prop(operator, "add_fake_user")
        body.prop(operator, "import_anims")


def menu_func_import(self, context):
    self.layout.operator_context = "INVOKE_DEFAULT"
    self.layout.operator(ImportBFRES.bl_idname, text="Nintendo Switch BFRES (.bfres/.szs/.zs)")


# def menu_func_export(self, context):
#    self.layout.operator(ExportBFRES.bl_idname, text="Nintendo Switch BFRES (.bfres)")


classes = (
    ImportBFRES,
    # ExportBFRES,
)

# define Blender functions


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    # bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    # bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    # main() # see above function
    register()
