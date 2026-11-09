"""Replace the scan's mosaic with the reference's small botanical print."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v385_shirt_print'
OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
mat = bpy.data.materials['V379_MUTED_PATTERN_SHIRT']
assert not mat.get('V385_print_applied')
nodes, links = mat.node_tree.nodes, mat.node_tree.links
shader = nodes['Principled BSDF']
image = bpy.data.images.load(str(ROOT / 'assets/generated/character_shirt_v385/muted_botanical_paisley_albedo.png'), check_existing=True)
image.pack()
position = nodes.new('ShaderNodeAttribute')
position.attribute_name = 'V372_RestPosition'
scale = nodes.new('ShaderNodeVectorMath')
scale.operation = 'SCALE'
scale.inputs['Scale'].default_value = 1. / .24
links.new(position.outputs['Vector'], scale.inputs[0])
texture = nodes.new('ShaderNodeTexImage')
texture.name = 'V385_BotanicalPrint'
texture.image = image
texture.projection = 'BOX'
texture.projection_blend = .15
texture.extension = 'REPEAT'
links.new(scale.outputs['Vector'], texture.inputs['Vector'])
links.new(texture.outputs['Color'], shader.inputs['Base Color'])
shader.inputs['Roughness'].default_value = .78
shader.inputs['Sheen Weight'].default_value = .08
mat['V385_print_applied'] = True
report = {'texture': image.filepath, 'tile_width_m': .24, 'rig_drivers': 1957,
          'status': 'Requires visual review on the character'}
(OUT / 'shirt_print_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
