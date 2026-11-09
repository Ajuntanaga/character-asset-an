"""Repair the legacy asset's subsurface conversion, without changing the rig."""
from pathlib import Path
import json
import bpy
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v374_natural_eyes'
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
m=bpy.data.materials['V374_PROCEDURAL_BROWN_EYE.001']
g=next(n for n in m.node_tree.nodes if n.type=='GROUP')
nt=g.node_tree
# Freeze the asset's static color/texture controls. Self-referencing material
# drivers from the Blender 3 asset introduce dependency cycles in Blender 5.
values=[]
if nt.animation_data:
 for d in list(nt.animation_data.drivers):
  assert d.driver.expression=='default_value' and len(d.driver.variables)==1
  target=d.driver.variables[0].targets[0]
  source=target.id
  if isinstance(source,bpy.types.Material): source=m
  values.append((d.data_path,d.array_index,source.path_resolve(target.data_path)))
 for path,index,value in values:
  nt.driver_remove(path,index)
  owner_path,attr=path.rsplit('.',1)
  owner=nt.path_resolve(owner_path)
  prop=getattr(owner,attr)
  if isinstance(prop,(float,int,bool)): setattr(owner,attr,value)
  else: prop[index]=value
bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
for link in list(bs.inputs['Subsurface Scale'].links): nt.links.remove(link)
bs.inputs['Subsurface Scale'].default_value=.0007
bs.inputs['Subsurface Weight'].default_value=.08
bs.inputs['Subsurface Radius'].default_value=(1.,.6,.4)
bs.inputs['Subsurface Anisotropy'].default_value=.0
# The original asset includes a lamp-specific iris displacement trick; keep
# the authored iris geometry and normal detail without that world-scale offset.
output=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
for link in list(output.inputs['Displacement'].links): m.node_tree.links.remove(link)
for side in ('L','R'):
 bpy.data.objects['V374_EYE.'+side].data.shape_keys.key_blocks['Dilation'].value=.08
bpy.context.view_layer.update()
scene=bpy.context.scene
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.cycles.samples=48
report={'static_material_drivers_resolved':len(values),'subsurface_scale_m':.0007,
        'subsurface_weight':.08,'pupil_dilation':.08,'rig_drivers':len(rig.animation_data.drivers)}
(OUT/'eye_shader_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_natural_eyes_v374b.blend'),compress=True)
scene.render.filepath=str(OUT/'v374b_eyes_open.png')
bpy.ops.render.render(write_still=True)
print(json.dumps(report))
