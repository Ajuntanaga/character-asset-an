import bpy,json
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'production_v412_conform_stitch';O.mkdir(exist_ok=True)
o=bpy.data.objects['V411_FITTED_CUFF.R'];st=bpy.data.objects['V411_Cuff_Stitches.R'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER')
mod=o.modifiers[0];enabled=mod.show_viewport
try:
 mod.show_viewport=False;bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
finally:mod.show_viewport=enabled;bpy.context.view_layer.update()
# Translate each tube endpoint ring onto the actual subdivision surface.
st.data=st.data.copy();dist=[]
for start in range(0,len(st.data.vertices),6):
 verts=list(st.data.vertices)[start:start+6];center=sum((v.co for v in verts),Vector())/6
 pos,normal,_,d=tree.find_nearest(center);offset=pos+normal*.00023-center;dist.append(d)
 for v in verts:v.co+=offset
kd=kdtree.KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(v.co,v.index)
kd.balance()
for v in st.data.vertices:
 for g in list(v.groups):st.vertex_groups[g.group].remove([v.index])
 _,idx,_=kd.find(v.co)
 for g in o.data.vertices[idx].groups:st.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
st.data.update();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
(O/'report.json').write_text(json.dumps({'maximum_stitch_correction_m':max(dist),'drivers':1957,'lit_review_pending':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_conform_stitch_v412.blend'),compress=True)
print('V412 saved',max(dist))
