import bpy, math, json
from pathlib import Path
from mathutils import Vector,kdtree
R=Path(__file__).resolve().parents[1];O=R/'production_v411_cuff_stitch';O.mkdir(exist_ok=True)
s=bpy.context.scene;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];src=bpy.data.objects['V410_CLEAN_CUFF.R']
assert not bpy.app.is_job_running('RENDER')
assert len(r.animation_data.drivers)==1957
assert 'V411_FITTED_CUFF.R' not in bpy.data.objects
o=src.copy();o.data=src.data.copy();o.name='V411_FITTED_CUFF.R';src.users_collection[0].objects.link(o)
# Retain sleeve join; reduce the lower opening by 8 percent.
for v in o.data.vertices:
 t=max(0,min(1,(.925-v.co.z)/.025));v.co.x=-.298+(v.co.x+.298)*(1-.08*t);v.co.y=.014+(v.co.y-.014)*(1-.08*t)
src.hide_render=True;src.hide_set(True)
# Transfer skinning from corresponding fitted sleeve vertices to stitch geometry.
kd=kdtree.KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(v.co,v.index)
kd.balance()
mat=bpy.data.materials.new('V411_Muted_Tan_Thread');mat.diffuse_color=(.22,.125,.054,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Roughness'].default_value=.82
vs=[];fs=[]
# Two rows at the lower opening and two defining the structured wrist band.
for z,rx,ry in ((.890,.025,.029),(.8925,.025,.029),(.910,.027,.034),(.9125,.028,.036)):
 for i in range(72):
  a=2*math.pi*i/72;b=a+2*math.pi/72*.58
  ends=[]
  for angle in (a,b):
   zz=z+.006*math.cos(angle)*max(0,min(1,(.925-z)/.03));t=max(0,min(1,(.925-zz)/.025));cx=-.298
   ends.append(Vector((cx+(rx+.00045)*math.cos(angle)*(1-.08*t),.014+(ry+.00045)*math.sin(angle)*(1-.08*t),zz)))
  axis=(ends[1]-ends[0]).normalized();rad=Vector((math.cos(a),math.sin(a),0));up=axis.cross(rad).normalized();base=len(vs)
  for p in ends:
   for k in range(6):vs.append(p+.00019*(rad*math.cos(k*math.tau/6)+up*math.sin(k*math.tau/6)))
  for k in range(6):fs.append((base+k,base+(k+1)%6,base+6+(k+1)%6,base+6+k))
m=bpy.data.meshes.new('V411_Individual_Stitches');m.from_pydata(vs,[],fs);m.materials.append(mat);m.update()
st=bpy.data.objects.new('V411_Cuff_Stitches.R',m);o.users_collection[0].objects.link(st)
for g in o.vertex_groups:st.vertex_groups.new(name=g.name)
for v in m.vertices:
 _,idx,_=kd.find(v.co)
 for g in o.data.vertices[idx].groups:st.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
for p in m.polygons:p.use_smooth=True
mod=st.modifiers.new('Existing CloudRig deformation','ARMATURE');mod.object=r;mod.use_deform_preserve_volume=True
bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'drivers':len(r.animation_data.drivers),'stitches':288,'fit_reduction':.08,'status':'lit_review_pending'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_cuff_stitch_v411.blend'),compress=True)
print('V411 saved')
