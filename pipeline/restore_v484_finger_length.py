import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v484_finger_length'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
def coords(s):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+s].evaluated_get(bpy.context.evaluated_depsgraph_get());a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
a={s:coords(s) for s in ('L','R')}
for n,m in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[n].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update()
report={'restored':True,'drivers':len(r.animation_data.drivers),'mesh_delta_local_mm':{s:float(np.max(np.linalg.norm(a[s]-coords(s),axis=1))*1000) for s in ('L','R')}}
(out/'restored.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
