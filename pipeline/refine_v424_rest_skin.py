"""Anchor hand pigment, roughness and pores to undeformed hand coordinates."""
from pathlib import Path
import json
import bpy
ROOT = Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
assert 'production_v423_joint_creases' in bpy.data.filepath
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
out = ROOT/'production_v424_rest_skin'
out.mkdir(exist_ok=True)
report = {}
for side in ('R','L'):
    hand = bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
    assert 'V423_rest_position' in hand.data.attributes
    slots = [s for s in hand.material_slots if s.material and s.material.name.startswith('V423_Joint_Detail')]
    assert len(slots) == 1
    material = slots[0].material.copy()
    material.name = 'V424_Rest_Skin.'+side
    nodes, links = material.node_tree.nodes, material.node_tree.links
    attribute = nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = 'V423_rest_position'
    attribute.label = 'Undeformed hand texture coordinates'
    noises = [n for n in nodes if n.type == 'TEX_NOISE']
    assert len(noises) == 3, len(noises)
    for noise in noises:
        links.new(attribute.outputs['Vector'], noise.inputs['Vector'])
        assert noise.inputs['Vector'].links[0].from_node == attribute
    slots[0].material = material
    report[side] = {'material': material.name, 'anchored_noise_nodes': [n.name for n in noises]}
report['rig_drivers'] = len(rig.animation_data.drivers)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_rest_skin_v424.blend'))
(out/'review.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
print('CAMERAS', [(o.name, list(o.location), o.data.type) for o in bpy.data.objects if o.type == 'CAMERA'])
