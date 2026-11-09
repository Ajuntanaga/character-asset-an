"""Finish the larger-hand trial with string clearance and centered pick thickness."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v468_hand_readability'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted();c=r.pose.bones['IK-Hand.R']
m=c.matrix.copy();m.translation+=r.matrix_world.inverted().to_3x3()@g.matrix_world.to_3x3()@Vector((0,0,.0006));c.matrix=m;r.update_tag();bpy.context.view_layer.update()
exec(compile((root/'pipeline/inspect_v458_pinch.py').read_text(),'pinch','exec'))
contact=report['thumb_contact'][0];center=(Vector(contact['point'])+Vector(contact['index_point']))*.5
p=bpy.data.objects['V361_NYLON_PICK'];(out/'original_pick_matrix.json').write_text(json.dumps([list(row) for row in p.matrix_world]))
t=gi@p.matrix_world;n=(t.to_3x3()@p.data.polygons[0].normal).normalized();q=t@p.data.polygons[0].center-n*.00035
delta=n*(center-q).dot(n);p.location+=g.matrix_world.to_3x3()@delta;bpy.context.view_layer.update()
report['pick_plane_shift_local']=list(delta);report['total_wrist_lift_m']=.0026
(out/'pinch.json').write_text(json.dumps(report,indent=2))
f=root/'pipeline/check_v458_grip_fit.py';exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v468_hand_readability/check.json'),str(f),'exec'))
assert not r['crossed_string_centrelines'] and r['sampled_clearance_m']>.0003
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v468_hand_readability/close.png','resolution':[900,700],'samples':24,'scale':.42,'camera':list(g.matrix_world@Vector((.68,.28,.42))),'target':list(g.matrix_world@Vector((.635,-.02,.045)))}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
