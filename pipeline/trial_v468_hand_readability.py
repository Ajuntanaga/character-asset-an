"""Compare reference-sized hand silhouettes while preserving fingertip anchors."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v468_hand_readability';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v466' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];original={};report={}
for side,factor in [('R',1.20),('L',1.08)]:
 c=r.pose.bones['IK-Hand.'+side];original[side]=[list(row) for row in c.matrix_basis]
 digits=('Index','Thumb') if side=='R' else ('Middle',)
 def anchor():return sum((r.pose.bones[f'DEF-Finger_{d}3.{side}'].tail.copy() for d in digits),Vector())/len(digits)
 before=anchor();c.scale*=factor;r.update_tag();bpy.context.view_layer.update()
 delta=before-anchor();m=c.matrix.copy();m.translation+=delta;c.matrix=m;r.update_tag();bpy.context.view_layer.update()
 report[side]={'factor':factor,'anchor_error_m':(anchor()-before).length,'wrist_shift_m':list(delta)}
(out/'original_pose.json').write_text(json.dumps(original));report['drivers']=len(r.animation_data.drivers);assert report['drivers']==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/check_v458_grip_fit.py';exec(compile(f.read_text().replace("production_v458_grip_fit/check.json","production_v468_hand_readability/check.json"),str(f),'exec'))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v468_hand_readability/full.png','resolution':[720,960],'samples':24,'scale':2.12,'camera':[.35,-3.5,1.3],'target':[0,0,.94]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
