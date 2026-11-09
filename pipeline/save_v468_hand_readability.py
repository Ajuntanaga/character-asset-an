import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v468_hand_readability'
assert not bpy.app.is_job_running('RENDER')
g=bpy.data.objects['V206_GUITAR_ROOT'];p=bpy.data.objects['V361_NYLON_PICK'];d=json.loads((out/'pinch.json').read_text())
m=Matrix(json.loads((out/'original_pick_matrix.json').read_text()));m.translation+=g.matrix_world.to_3x3()@Vector(d['pick_plane_shift_local']);p.matrix_world=m
bpy.context.view_layer.update()
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
s=bpy.context.scene;s.render.resolution_x=720;s.render.resolution_y=960;s.camera.data.ortho_scale=2.12;s.camera.location=(.35,-3.5,1.3);s.camera.rotation_euler=(Vector((0,0,.94))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/'final_full.png')
dest=out/'Character_An_hand_readability_v468.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
print(json.dumps({'saved':str(dest),'drivers':1957,'pick_parent':p.parent.name if p.parent else None,'pick_plane_shift_local':d['pick_plane_shift_local']}))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v468_hand_readability/final_full.png','resolution':[720,960],'samples':24,'scale':2.12,'camera':[.35,-3.5,1.3],'target':[0,0,.94]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
