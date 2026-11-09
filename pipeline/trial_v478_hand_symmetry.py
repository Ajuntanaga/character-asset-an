"""Equalize posed hand scales, preserving the left middle fingertip anchor."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v478_hand_symmetry';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v477' in bpy.data.filepath
assert not (out/'original_pose.json').exists(), 'Do not accumulate scale corrections'
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];c=r.pose.bones['IK-Hand.L'];right=r.pose.bones['IK-Hand.R']
(out/'original_pose.json').write_text(json.dumps([list(row) for row in c.matrix_basis]))
def anchor():return r.pose.bones['DEF-Finger_Middle3.L'].tail.copy()
before=anchor();factor=right.scale.x/c.scale.x;c.scale*=factor
r.update_tag();bpy.context.view_layer.update()
m=c.matrix.copy();m.translation+=before-anchor();c.matrix=m
r.update_tag();bpy.context.view_layer.update()
report={'factor':factor,'anchor_error_mm':(anchor()-before).length*1000,'drivers':len(r.animation_data.drivers),'left_scale':list(c.scale),'right_scale':list(right.scale)}
assert report['drivers']==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v478_hand_symmetry/full.png','resolution':[720,960],'samples':24,'scale':2.12,'camera':[.35,-3.5,1.3],'target':[0,0,.94]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
