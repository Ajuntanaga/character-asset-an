from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
for control in ('Blink.L','Blink.R','JawOpen','Smile.L','Smile.R'): rig.pose.bones['Head'][control]=0.0
rig.update_tag()
bpy.context.view_layer.update()
s=bpy.context.scene
s.camera.location=(0,-1.4,1.64)
s.camera.rotation_euler=(Vector((0,0,1.64))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.camera.data.ortho_scale=.37
s.render.resolution_x=s.render.resolution_y=700
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'production_v399_oral_materials/Character_An_oral_materials_v399.blend'),compress=True)
print(json.dumps({'saved':bpy.data.filepath,'rig_drivers':len(rig.animation_data.drivers),'blink':[rig.pose.bones['Head']['Blink.'+x] for x in ('L','R')]}))
