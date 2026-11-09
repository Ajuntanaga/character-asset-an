"""Replace periodic guitar bands with irregular fine figured maple."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v387_maple_veneer'
OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
mat = bpy.data.materials['V356_GRAYBURST_FLAMED_MAPLE']
assert not mat.get('V387_veneer_applied')
nodes,links = mat.node_tree.nodes,mat.node_tree.links
mix = next(n for n in nodes if n.type == 'MIX_RGB')
uv = nodes.new('ShaderNodeUVMap')
uv.uv_map = 'WoodProjection'
separate = nodes.new('ShaderNodeSeparateXYZ')
combine = nodes.new('ShaderNodeCombineXYZ')
links.new(uv.outputs['UV'],separate.inputs[0])
# Image vertical grain follows the guitar's longitudinal X axis.
links.new(separate.outputs['Y'],combine.inputs['X'])
links.new(separate.outputs['X'],combine.inputs['Y'])
image = bpy.data.images.load(str(ROOT/'assets/generated/gray_maple_v387/gray_curly_maple_albedo.png'),check_existing=True)
image.pack()
texture = nodes.new('ShaderNodeTexImage')
texture.name = 'V387_FiguredMaple'
texture.image = image
texture.extension = 'EXTEND'
links.new(combine.outputs[0],texture.inputs['Vector'])
tint = nodes.new('ShaderNodeMixRGB')
tint.name = 'V387_GrayStain'
tint.blend_type = 'MULTIPLY'
tint.inputs[0].default_value = 1.
tint.inputs[2].default_value = (.65,.70,.67,1.)
links.new(texture.outputs['Color'],tint.inputs[1])
links.new(tint.outputs[0],mix.inputs[2])
mat['V387_veneer_applied'] = True
report = {'image':image.filepath,'geometry_changed':False,'rig_drivers':1957}
(OUT/'veneer_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_maple_veneer_v387.blend'),compress=True)
print(json.dumps(report))
