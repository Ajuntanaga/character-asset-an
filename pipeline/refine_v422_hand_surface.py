"""Non-destructive skin material candidate; retain V421 geometry and rig."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'production_v422_hand_surface';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
source=bpy.data.materials['V351_Warm_Brown_Hand_Skin']
m=source.copy();m.name='V422_Varied_Hand_Skin'
n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');base=list(p.inputs['Base Color'].default_value)
p.inputs['IOR'].default_value=1.4
p.inputs['Subsurface Weight'].default_value=.12
p.inputs['Subsurface Radius'].default_value=(1,.42,.22)
p.inputs['Subsurface Scale'].default_value=.0012
tex=n.get('Texture Coordinate')
def noise(name,scale,detail):
 a=n.new('ShaderNodeTexNoise');a.name=name;a.inputs['Scale'].default_value=scale;a.inputs['Detail'].default_value=detail;l.new(tex.outputs['Object'],a.inputs['Vector']);return a
variation=noise('Subtle pigment variation',95,3)
r=n.new('ShaderNodeValToRGB');r.name='Warm tonal variation'
r.color_ramp.elements[0].position=.18;r.color_ramp.elements[0].color=tuple(base[i]*[.88,.83,.8][i] for i in range(3))+(1,)
r.color_ramp.elements[1].position=.82;r.color_ramp.elements[1].color=tuple(min(1,base[i]*[1.08,1.06,1.03][i]) for i in range(3))+(1,)
l.new(variation.outputs['Fac'],r.inputs['Fac']);l.new(r.outputs['Color'],p.inputs['Base Color'])
rough=noise('Fine roughness variation',420,2)
r2=n.new('ShaderNodeMapRange');r2.name='Skin roughness range';r2.inputs['To Min'].default_value=.48;r2.inputs['To Max'].default_value=.64
l.new(rough.outputs['Fac'],r2.inputs['Value']);l.new(r2.outputs['Result'],p.inputs['Roughness'])
n.get('Noise Texture').inputs['Scale'].default_value=1600
n.get('Bump').inputs['Strength'].default_value=.2
n.get('Bump').inputs['Distance'].default_value=.00008
nail=bpy.data.materials['V351_Natural_Keratin_Nails'].copy();nail.name='V422_Satin_Keratin_Nails'
np=nail.node_tree.nodes.get('Principled BSDF');np.inputs['Roughness'].default_value=.38;np.inputs['Coat Weight'].default_value=.04;np.inputs['Coat Roughness'].default_value=.25
for name in ['V357_ANATOMICAL_HAND.R','V357_ANATOMICAL_HAND.L']:
 o=bpy.data.objects[name]
 for i,old in enumerate(o.data.materials):
  if old==source:o.data.materials[i]=m
  elif old.name=='V351_Natural_Keratin_Nails':o.data.materials[i]=nail
report={'base_color':base,'drivers':len(rig.animation_data.drivers),'geometry_changed':False,'status':'pending visual review','limitation':'Anatomical creases remain to be sculpted; procedural pigment is surface variation only.'}
(out/'review.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_hand_surface_v422.blend'),compress=True)
print(json.dumps(report))
