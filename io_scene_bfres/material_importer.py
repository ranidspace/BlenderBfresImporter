from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
import bpy
import logging
import mathutils

from .bfrespy.common import ResString

log = logging.getLogger(__name__)


class MaterialImporter:
    """Imports material from FMDL."""

    def __init__(self, parent, fmdl):
        self.fmdl = fmdl
        self.operator = parent.operator
        self.context = parent.context
        self.texture_map: dict

    def import_material(self, fmat, texture_dict, material_dict):
        """Import specified material from fmat."""
        mat = bpy.data.materials.new(name=fmat.name)
        material_dict[fmat.name] = mat
        mat.name
        mat.use_nodes = True
        mat_wrap = PrincipledBSDFWrapper(mat, is_readonly=False)
        self.__add_custom_properties(fmat, mat)

        mappingnode = None
        i = 0
        for sampler, tex_sampler in fmat.samplers.items():
            texName = fmat.texture_refs[i].name
            if (texName in texture_dict):
                image = texture_dict[texName]
            else:
                image = bpy.data.images.get(texName)
            
            if (image is None):
                log.warning("Missing Texture: '%s'",
                            texName)
                continue


            tex_sampler_name = fmat.shader_assign.sampler_assigns.try_get_key(ResString(sampler))
            i += 1

            # Get the bpy Texture Wrapper from the sampler name
            tex_helper_name = self._get_tex_wrapper.get(tex_sampler_name)
            if (tex_helper_name):
                tex_helper = getattr(mat_wrap, tex_helper_name)
                tex_helper.image = image
            else:
                # Add the texture as a node not connected to anything if no samplers match
                tex_node = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
                log.warning("Unused texture: %s", texName)
                tex_node.location = mathutils.Vector((mat_wrap._grid_to_location(1, -2)))
                tex_node.label = f"{tex_sampler_name} {texName}"
                tex_node.image = image
                continue

            # Mapping
            if (mat.get('MP_tex_mtx0_mode')):
                if (mappingnode is None):
                    loc = mat['MP_tex_mtx0_translation']
                    tex_helper.translation = mathutils.Vector((loc[0], loc[1], 0))

                    rot = mat['MP_tex_mtx0_rotation']
                    tex_helper.rotation = mathutils.Vector((0, 0, rot))

                    scale = mat['MP_tex_mtx0_scaling']
                    scalemode = mat['MP_tex_mtx0_mode']
                    # XXX Needs improvement
                    match scalemode:
                        case 'MODE_MAYA':
                            scalevec = (1 / scale[0], 1 / scale[1], 1)
                        case _:
                            scalevec = (scale[0], scale[1], 1)
                    tex_helper.scale = mathutils.Vector(scalevec)

                    mappingnode = tex_helper.node_mapping
                else:
                    mat.node_tree.links.new(mappingnode.outputs['Vector'], tex_helper.node_image.inputs['Vector'])

        match fmat.shader_assign.shader_archive_name:
            case 'Hoian_UBER':
                self.__shader_hoian(mat, mat_wrap)

    _get_tex_wrapper = {
        '_a0': 'base_color_texture',
        '_r0': 'roughness_texture',
        '_m0': 'metallic_texture',
        '_n0': 'normalmap_texture',
        '_e0': 'emission_color_texture',
        '_op0': 'alpha_texture',
    }

    @staticmethod
    def __add_custom_properties(fmat, mat: bpy.types.Material):
        """Add render/shader/material parameters and sampler list
        as custom properties on the Blender material object.
        """

        # Make Render Info
        for name, param in fmat.renderinfos.items():
            val = param.data
            if (len(param.data) == 1):
                val = val[0]
            mat["RI_" + name] = val

        # Make Material Params
        for name, param in fmat.shaderparams.items():
            pname = 'MP_' + name
            if (param.type.name in ('TEX_SRT', 'TEX_SRT_EX')):
                mat[pname + "_mode"] = param.data_value.mode.name
                mat[pname + "_scaling"] = param.data_value.scaling
                mat[pname + "_rotation"] = param.data_value.rotation
                mat[pname + '_translation'] = param.data_value.translation

                propman = mat.id_properties_ui(pname + "_scaling")
                propman.update(subtype='XYZ')
                propman = mat.id_properties_ui(pname + "_rotation")
                propman.update(subtype='ANGLE')
                propman = mat.id_properties_ui(pname + "_translation")
                propman.update(subtype='XYZ')
            else:
                mat[pname] = param.data_value
                if (param.type.name == "FLOAT4"):
                    propman = mat.id_properties_ui(pname)
                    propman.update(subtype="COLOR_GAMMA", min=0, max=1, step=0.01)

        for name, val in fmat.shader_assign.shaderoptions.items():
            mat['SO_' + name] = str(val)

        mat['samplers'] = {
            key: str(value) for key, value in fmat.shader_assign.sampler_assigns.items()
        }

    @staticmethod
    def __shader_hoian(mat, mat_wrap: PrincipledBSDFWrapper):
        # Small changes for Splatoon 3 shaders
        if mat.get('SO_enable_albedo_tex') == 'false':
            mat_wrap.base_color = mat['MP_albedo_color'][:3]

        if mat.get('SO_enable_roughness_map') != 'true':
            mat_wrap.roughness = mat['MP_roughness']

        if mat.get('SO_enable_metalness_map') != 'true':
            mat_wrap.metallic = mat['MP_metalness']

        if mat.get('SO_enable_opacity_tex') != 'true':
            mat_wrap.alpha = mat['MP_opacity']

        if mat.get('SO_enable_emission_map') != 'true':
            mat_wrap.emission_color = mat['MP_emission_color'][:3]

        if mat.get('SO_emission_color_type') == '1':
            mat_wrap.emission_color_texture.image = mat_wrap.base_color_texture.image

        if mat.get('SO_enable_emission') == 'true':
            mat_wrap.emission_strength = mat['MP_emission_intensity']
