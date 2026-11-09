import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v465_joint_weights'
assert not bpy.app.is_job_running('RENDER')
o=bpy.data.objects['V357_ANATOMICAL_HAND.R']
for v,w in zip(o.data.vertices,json.loads((out/'original_weights.json').read_text())):
 for entry in list(v.groups):o.vertex_groups[entry.group].remove([v.index])
 for name,value in w.items():o.vertex_groups[name].add([v.index],value,'REPLACE')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
for name,m in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[name].matrix_basis=Matrix(m)
o.data.update();o.update_tag();r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
print('Original weights and playing pose restored; 1957 drivers preserved')
