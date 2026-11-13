"""Compare original skin with an eye-local shader patch; never save production."""
from pathlib import Path
import hashlib
import json
import runpy
import bpy

original = Path('Character_An_photoreal_head_basecolor_v326.png')
trial = Path('references/derived/eyelid_albedo_v745/Character_An_eyelid_albedo_TRIAL_v745.png')
assert hashlib.sha256(trial.read_bytes()).hexdigest() == '1b8cb0746c98547e78f9b7872a1b6b2a6dc4d71031a928ece7b659f2c3bb2802'
renderer = Path(__file__).with_name('render_v740_cloud_groom.py')

def render(label):
    for pose, blink in [('rest', 0.), ('blink', 1.)]:
        runpy.run_path(str(renderer), init_globals={
            'TEXTURE_PATH': str(original),
            'POSE': {'Blink.L': blink, 'Blink.R': blink},
            'TAG': 'v745_eyelid_' + label + '_' + pose,
            'VIEWS': ['front'], 'SAMPLES': 24,
        })

render('control_local')
# Atlas coordinates are initial visual estimates, to be judged in both poses.
centers = [(.455, .557, 0.), (.544, .557, 0.)]
radii = (.026, .016)
patched = 0
seen_materials = set()
for material in bpy.data.objects['V740_NATIVE_FACE'].data.materials:
    if not material or not material.use_nodes:
        continue
    if material.name in seen_materials:
        continue
    seen_materials.add(material.name)
    tree = material.node_tree
    sources = [n for n in tree.nodes if n.type == 'TEX_IMAGE' and n.image
               and Path(n.image.filepath).name == original.name]
    for source in sources:
        destinations = [link.to_socket for link in source.outputs['Color'].links]
        if not destinations:
            continue
        uv = tree.nodes.new('ShaderNodeTexCoord')
        vector = source.inputs['Vector'].links[0].from_socket if source.inputs['Vector'].is_linked else uv.outputs['UV']
        patch = tree.nodes.new('ShaderNodeTexImage')
        patch.image = bpy.data.images.load(str(trial.resolve()), check_existing=True)
        tree.links.new(vector, patch.inputs['Vector'])
        masks = []
        for center in centers:
            subtract = tree.nodes.new('ShaderNodeVectorMath')
            subtract.operation = 'SUBTRACT'
            subtract.inputs[1].default_value = center
            tree.links.new(vector, subtract.inputs[0])
            scale = tree.nodes.new('ShaderNodeVectorMath')
            scale.operation = 'MULTIPLY'
            scale.inputs[1].default_value = (1/radii[0], 1/radii[1], 0.)
            tree.links.new(subtract.outputs['Vector'], scale.inputs[0])
            length = tree.nodes.new('ShaderNodeVectorMath')
            length.operation = 'LENGTH'
            tree.links.new(scale.outputs['Vector'], length.inputs[0])
            ramp = tree.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.interpolation = 'EASE'
            ramp.color_ramp.elements[0].position = .75
            ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
            ramp.color_ramp.elements[1].position = 1.
            ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
            tree.links.new(length.outputs['Value'], ramp.inputs['Fac'])
            masks.append(ramp.outputs['Color'])
        union = tree.nodes.new('ShaderNodeMath')
        union.operation = 'MAXIMUM'
        for i, mask in enumerate(masks):
            tree.links.new(mask, union.inputs[i])
        mix = tree.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MIX'
        tree.links.new(union.outputs[0], mix.inputs[0])
        tree.links.new(source.outputs['Color'], mix.inputs[1])
        tree.links.new(patch.outputs['Color'], mix.inputs[2])
        for destination in destinations:
            tree.links.new(mix.outputs[0], destination)
        patched += 1
assert patched, 'No original atlas color links were patched'
render('localized')
Path('results/renders/v745_eyelid_localized_mask.json').write_text(json.dumps({
    'centers_uv': centers, 'radii_uv': radii, 'full_weight_radius': .75,
    'patched_nodes': patched, 'original_preserved_outside_masks': True,
    'production_saved': False, 'visual_acceptance': 'pending',
}, indent=2))
