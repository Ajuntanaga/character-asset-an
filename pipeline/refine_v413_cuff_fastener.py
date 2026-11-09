import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'production_v413_cuff_fastener';O.mkdir(exist_ok=True)
s=bpy.context.scene;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];o=bpy.data.objects['V411_FITTED_CUFF.R'];st=bpy.data.objects['V411_Cuff_Stitches.R']
assert not bpy.app.is_job_running('RENDER');assert len(r.animation_data.drivers)==1957
assert 'V413_Brass_Cuff_Button.R' not in bpy.data.objects
# Outer ring faces must point away from the wrist center.
p=o.data.polygons[4*96];rad=Vector((p.center.x+.298,p.center.y-.014,0));flipped=p.normal.dot(rad)<0
if flipped:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
mod=o.modifiers[0];enabled=mod.show_viewport
try:
 mod.show_viewport=False;bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
finally:mod.show_viewport=enabled;bpy.context.view_layer.update()
for start in range(0,len(st.data.vertices),6):
 vv=[st.data.vertices[i] for i in range(start,start+6)];c=sum((v.co for v in vv),Vector())/6;pos,n,_,d=tree.find_nearest(c)
 if n.dot(Vector((pos.x+.298,pos.y-.014,0)))<0:n=-n
 for v in vv:v.co+=pos+n*.00023-c
# A small pressed brass button, built in rest space and skinned with the cuff.
a=math.radians(235);q=Vector((-.298+.025*math.cos(a),.014+.032*math.sin(a),.900));pos,n,_,_=tree.find_nearest(q)
if n.dot(Vector((pos.x+.298,pos.y-.014,0)))<0:n=-n
u=n.cross(Vector((0,0,1))).normalized();v=n.cross(u).normalized();verts=[];faces=[]
profile=[(0,.0008),(.0035,.0008),(.0045,.0011),(.0049,.0017),(.0046,.0023),(.0039,.0024),(.0035,.0018),(0,.0018)]
for radius,depth in profile:
 for i in range(48):
  t=i*math.tau/48;verts.append(pos+n*depth+radius*(u*math.cos(t)+v*math.sin(t)))
for j in range(len(profile)-1):
 for i in range(48):faces.append((j*48+i,j*48+(i+1)%48,(j+1)*48+(i+1)%48,(j+1)*48+i))
m=bpy.data.meshes.new('V413_Pressed_Brass_Button');m.from_pydata(verts,[],faces);m.update();button=bpy.data.objects.new('V413_Brass_Cuff_Button.R',m);o.users_collection[0].objects.link(button)
mat=bpy.data.materials.new('V413_Aged_Brass');mat.diffuse_color=(.26,.16,.055,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Metallic'].default_value=.85;bs.inputs['Roughness'].default_value=.39;m.materials.append(mat)
kd=kdtree.KDTree(len(o.data.vertices))
for vert in o.data.vertices:kd.insert(vert.co,vert.index)
kd.balance();_,idx,_=kd.find(pos)
for g in o.vertex_groups:button.vertex_groups.new(name=g.name)
for g in o.data.vertices[idx].groups:button.vertex_groups[g.group].add(list(range(len(verts))),g.weight,'REPLACE')
arm=button.modifiers.new('Existing CloudRig deformation','ARMATURE');arm.object=r;arm.use_deform_preserve_volume=True
for p in m.polygons:p.use_smooth=True
st.data.update();bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'outer_normals_flipped':flipped,'button_diameter_mm':9.8,'drivers':len(r.animation_data.drivers)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_cuff_fastener_v413.blend'),compress=True)
engine,path=s.render.engine,s.render.filepath
try:
 s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v413_pick_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path
print('V413 saved; outer normals flipped:',flipped)
