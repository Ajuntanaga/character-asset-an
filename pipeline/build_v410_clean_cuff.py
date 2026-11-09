import bpy, math, json
from pathlib import Path
from mathutils import Vector, kdtree
R=Path(__file__).resolve().parents[1];O=R/'production_v410_clean_cuff';O.mkdir(exist_ok=True)
s=bpy.context.scene;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];old=bpy.data.objects['V357_CUFF_PATCH.R']
assert not bpy.app.is_job_running('RENDER')
assert len(r.animation_data.drivers)==1957
assert 'V410_CLEAN_CUFF.R' not in bpy.data.objects
kd=kdtree.KDTree(len(old.data.vertices))
for v in old.data.vertices:kd.insert(v.co,v.index)
kd.balance()
# Smooth tailored sleeve taper, with a rounded folded opening and inner return.
sections=[(.945,.294,.026,.046,.069),(.937,.295,.023,.041,.060),(.925,.296,.019,.034,.047),(.913,.297,.016,.028,.036),(.904,.298,.014,.025,.030),(.894,.298,.014,.025,.029),(.888,.298,.014,.025,.029),(.8865,.298,.014,.0245,.0285),(.886,.298,.014,.0235,.0275),(.887,.298,.014,.0225,.0265),(.895,.298,.014,.0225,.0265)]
N=96;vs=[];fs=[]
for z,cx,cy,rx,ry in sections:
 for i in range(N):
  a=2*math.pi*i/N
  # Opening follows the wrist's oblique cut instead of a flat pipe edge.
  tilt=.006*math.cos(a)*max(0,min(1,(.925-z)/.03))
  vs.append((-cx+rx*math.cos(a),cy+ry*math.sin(a),z+tilt))
for j in range(len(sections)-1):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
m=bpy.data.meshes.new('V410_Tailored_Cuff_Quads');m.from_pydata(vs,[],fs);m.update()
o=bpy.data.objects.new('V410_CLEAN_CUFF.R',m);old.users_collection[0].objects.link(o);o.matrix_world=old.matrix_world.copy()
for mat in old.data.materials:m.materials.append(mat)
for p in m.polygons:p.use_smooth=True;p.material_index=int(p.index//N>=8)
for g in old.vertex_groups:o.vertex_groups.new(name=g.name)
for v in m.vertices:
 neighbors=kd.find_n(v.co,4);weights={};total=0
 for co,idx,d in neighbors:
  factor=1/max(d,.0001)**2;total+=factor
  for g in old.data.vertices[idx].groups:weights[g.group]=weights.get(g.group,0)+factor*g.weight
 for idx,w in weights.items():o.vertex_groups[idx].add([v.index],w/total,'REPLACE')
a=o.modifiers.new('Existing CloudRig deformation','ARMATURE');a.object=r;a.use_deform_preserve_volume=True
sub=o.modifiers.new('Tailored surface smoothing','SUBSURF');sub.levels=1;sub.render_levels=2
old.hide_render=True;old.hide_set(True)
bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'source_preserved':old.name,'vertices':len(vs),'quads':len(fs),'drivers':len(r.animation_data.drivers),'status':'candidate_requires_visual_review'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_clean_cuff_v410.blend'),compress=True)
engine,path=s.render.engine,s.render.filepath
try:
 s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v410_pick_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path
print('V410 saved and diagnostic rendered')
