"""Restore playing controls and save the visually reviewed intermediate shape."""
import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v466_dorsal_anatomy'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
for name,matrix in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[name].matrix_basis=Matrix(matrix)
r.update_tag();bpy.context.view_layer.update();assert len(r.animation_data.drivers)==1957
s=bpy.context.scene;s.render.resolution_x=720;s.render.resolution_y=960;s.camera.data.ortho_scale=2.12;s.camera.location=(.35,-3.5,1.3);s.camera.rotation_euler=(Vector((0,0,.94))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(out/'full.png')
destination=out/'Character_An_hand_anatomy_v466.blend';assert not destination.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
print(json.dumps({'saved':bpy.data.filepath,'drivers':len(r.animation_data.drivers),'pose':'original playing pose','status':'intermediate anatomy improvement; full-view size and rigid knuckles unresolved'}))
