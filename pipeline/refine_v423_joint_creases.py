"""Rest-coordinate knuckle crease shader; does not alter silhouette or rig."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'production_v423_joint_creases';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
source=bpy.data.materials['V422_Varied_Hand_Skin']
# One readable group reused at each joint. The crease ends fade before finger sides.
g=bpy.data.node_groups.new('V423_Tapered_Joint_Folds','ShaderNodeTree')
for name,typ,io in [('Rest','NodeSocketVector','INPUT'),('Center','NodeSocketVector','INPUT'),('Axis','NodeSocketVector','INPUT'),('Across','NodeSocketVector','INPUT'),('Width','NodeSocketFloat','INPUT'),('Height','NodeSocketFloat','OUTPUT')]:g.interface.new_socket(name=name,in_out=io,socket_type=typ)
n=g.nodes;l=g.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput')
def mathnode(op,a,b=None):
 q=n.new('ShaderNodeMath');q.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):q.inputs[i].default_value=v
  else:l.new(v,q.inputs[i])
 return q.outputs[0]
def vec(op,a,b):
 q=n.new('ShaderNodeVectorMath');q.operation=op;l.new(a,q.inputs[0]);l.new(b,q.inputs[1]);return q.outputs['Value' if op=='DOT_PRODUCT' else 'Vector']
def fade(value,lo,hi):
 q=n.new('ShaderNodeMapRange');q.interpolation_type='SMOOTHERSTEP';l.new(value,q.inputs['Value']);q.inputs['From Min'].default_value=lo;q.inputs['From Max'].default_value=hi;q.inputs['To Min'].default_value=1;q.inputs['To Max'].default_value=0;return q.outputs['Result']
delta=vec('SUBTRACT',inp.outputs['Rest'],inp.outputs['Center'])
along=vec('DOT_PRODUCT',delta,inp.outputs['Axis']);across=vec('DOT_PRODUCT',delta,inp.outputs['Across'])
normalized=mathnode('DIVIDE',across,inp.outputs['Width'])
taper=fade(mathnode('ABSOLUTE',normalized),.4,1)
# Slight curved fold rather than a straight engraved ring.
curve=mathnode('MULTIPLY',mathnode('MULTIPLY',normalized,normalized),.0007)
along=mathnode('ADD',along,curve)
bands=[]
for offset,weight in [(0,1),(-.00165,.45),(.00165,.4)]:
 band=fade(mathnode('ABSOLUTE',mathnode('ADD',along,offset)),.00008,.00048)
 bands.append(mathnode('MULTIPLY',band,weight))
height=mathnode('MULTIPLY',mathnode('ADD',mathnode('ADD',bands[0],bands[1]),bands[2]),taper)
l.new(height,out.inputs['Height'])
report={}
for side in ['R','L']:
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 for name,values in [('V423_rest_position',[v.co[:] for v in o.data.vertices]),('V423_rest_normal',[v.normal[:] for v in o.data.vertices])]:
  a=o.data.attributes.get(name) or o.data.attributes.new(name,'FLOAT_VECTOR','POINT')
  a.data.foreach_set('vector',[x for v in values for x in v])
 m=source.copy();m.name='V423_Joint_Detail.'+side;n=m.node_tree.nodes;l=m.node_tree.links
 rest=n.new('ShaderNodeAttribute');rest.attribute_name='V423_rest_position'
 normal=n.new('ShaderNodeAttribute');normal.attribute_name='V423_rest_normal'
 sep=n.new('ShaderNodeSeparateXYZ');l.new(normal.outputs['Vector'],sep.inputs[0])
 # Limit detail to back and palm; avoid encircling each finger with a groove.
 mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(sep.outputs['Y'],mask.inputs[0]);l.new(sep.outputs['Y'],mask.inputs[1])
 transform=o.matrix_world.inverted()@rig.matrix_world
 total=None;count=0
 for digit in ['Thumb','Index','Middle','Ring','Pinky']:
  for index in [1,2,3]:
   if digit=='Thumb' and index==1:continue
   b=rig.data.bones[f'DEF-Finger_{digit}{index}.{side}'];center=transform@b.head_local;axis=(transform@b.tail_local-center).normalized()
   across=axis.cross(Vector((0,-1,0))).normalized()
   q=n.new('ShaderNodeGroup');q.node_tree=g;q.label=f'{digit} joint {index}'
   l.new(rest.outputs['Vector'],q.inputs['Rest']);q.inputs['Center'].default_value=center;q.inputs['Axis'].default_value=axis;q.inputs['Across'].default_value=across
   q.inputs['Width'].default_value=(.0065 if digit=='Pinky' else .0085) * (1.2 if index==1 else 1)
   if total is None:total=q.outputs['Height']
   else:
    add=n.new('ShaderNodeMath');add.operation='MAXIMUM';l.new(total,add.inputs[0]);l.new(q.outputs['Height'],add.inputs[1]);total=add.outputs[0]
   count+=1
 mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(total,mul.inputs[0]);l.new(mask.outputs[0],mul.inputs[1])
 bump=n.new('ShaderNodeBump');bump.name='Shallow joint folds';bump.invert=True;bump.inputs['Distance'].default_value=.00032;bump.inputs['Strength'].default_value=.55
 l.new(mul.outputs[0],bump.inputs['Height']);l.new(n.get('Bump').outputs['Normal'],bump.inputs['Normal']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
 for slot in o.material_slots:
  if slot.material==source:slot.material=m
 report[side]={'joints':count,'rest_attribute_vertices':len(o.data.vertices)}
report['drivers']=len(rig.animation_data.drivers);report['status']='awaiting lit and open pose review'
(OUT/'review.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_joint_creases_v423.blend'),compress=True)
print(json.dumps(report))
