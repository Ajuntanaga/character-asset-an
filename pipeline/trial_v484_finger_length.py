"""Reversible finger-to-palm proportion trial; preserve picking thumb/index."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v484_finger_length';out.mkdir(exist_ok=True)
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER') and 'v483' in bpy.data.filepath
assert not (out/'original_pose.json').exists()
names=[f'FK-Finger_{f}{j}.{s}' for s in ('L','R') for f in (('Index','Middle','Ring','Pinky') if s=='L' else ('Middle','Ring','Pinky')) for j in (1,2,3)]
backup={n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names}
(out/'original_pose.json').write_text(json.dumps(backup))
before={n:r.pose.bones[n.replace('FK-','DEF-')].length for n in names}
for n in names:r.pose.bones[n].scale.y*=1.12
r.update_tag();bpy.context.view_layer.update()
report={'drivers':len(r.animation_data.drivers),'lengths':{n:{'before':before[n],'after':r.pose.bones[n.replace('FK-','DEF-')].length} for n in names}}
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v484_finger_length/full.png','resolution':[720,960],'samples':24,'scale':2.12,'camera':[.35,-3.5,1.3],'target':[0,0,.94]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
