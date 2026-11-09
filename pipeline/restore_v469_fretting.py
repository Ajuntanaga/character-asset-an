import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v469_fretting'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];original=json.loads((out/'original_pose.json').read_text())
(out/'rejected_pose.json').write_text(json.dumps({n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in original},indent=2))
for n,m in original.items():r.pose.bones[n].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update();assert len(r.animation_data.drivers)==1957
s=bpy.context.scene;s.camera.location=(.35,-3.5,1.3);s.camera.rotation_euler=(Vector((0,0,.94))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=2.12;s.render.resolution_x=720;s.render.resolution_y=960;s.render.filepath=str(root/'production_v468_hand_readability/final_full.png')
err=max(abs(r.pose.bones[n].matrix_basis[i][j]-m[i][j]) for n,m in original.items() for i in range(4) for j in range(4));assert err<1e-6
print(json.dumps({'restored':True,'max_basis_error':err,'drivers':1957,'saved_checkpoint':bpy.data.filepath}))
