import bpy,json,math
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v484_finger_length';r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER')
for n,m in json.loads((out/'original_pose.json').read_text()).items():
 b=r.pose.bones[n];b.matrix_basis=Matrix(m)
 if n.split('.')[0].endswith('1'):b.scale.y*=1.12
r.update_tag();bpy.context.view_layer.update()
report={'status':'CANDIDATE_REQUIRES_OPEN_CURL_REVIEW','drivers':len(r.animation_data.drivers),'hands':{}}
for s in ('L','R'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+s].evaluated_get(bpy.context.evaluated_depsgraph_get())
 report['hands'][s]={'vertices':len(o.data.vertices),'finite':all(math.isfinite(c) for v in o.data.vertices for c in v.co)}
assert report['drivers']==1957 and all(v['finite'] for v in report['hands'].values())
p=out/'Character_An_finger_length_candidate_v484.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'candidate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
