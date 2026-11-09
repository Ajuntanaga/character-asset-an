"""Relax unused picking fingers while preserving the grip controls."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v406_pick_relax';O.mkdir(exist_ok=True)
s=bpy.context.scene;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER')
assert len(r.animation_data.drivers)==1957
before={b.name:list(b.rotation_euler) for b in r.pose.bones if b.name.startswith('FK-Finger_') and b.name.endswith('.R')}
for finger,angles in {'Middle':(35,57,26),'Ring':(40,63,30),'Pinky':(45,69,34)}.items():
 for i,angle in enumerate(angles,1):r.pose.bones[f'FK-Finger_{finger}{i}.R'].rotation_euler.x=math.radians(angle)
r.update_tag();bpy.context.view_layer.update()
(O/'pose_before.json').write_text(json.dumps(before,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_pick_relax_v406.blend'),compress=True)
old=(s.render.engine,s.render.filepath)
try:
 s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v406_pick_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath=old
print('V406 saved and diagnostic rendered; drivers',len(r.animation_data.drivers))
