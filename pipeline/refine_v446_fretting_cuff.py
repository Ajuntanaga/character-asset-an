"""Reduce fretting cuff flare with a continuous rest-space falloff."""
import bpy, math, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'production_v446_fretting_cuff';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_cuff_fabric_v445.blend')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
o=bpy.data.objects['V357_CUFF_PATCH.L']
o.data=o.data.copy()
a=rig.data.bones['DEF-Forearm_2.L'].head_local
b=rig.data.bones['DEF-Forearm_2.L'].tail_local
axis=b-a
changed=0;maximum=0
for v in o.data.vertices:
 p=o.matrix_world@v.co
 if not .865<p.z<.942:continue
 w=math.sin(math.pi*(p.z-.865)/.077)**2
 c=a+axis*((p-a).dot(axis)/axis.length_squared)
 delta=o.matrix_world.inverted().to_3x3()@((c-p)*(.16*w))
 v.co+=delta;changed+=1;maximum=max(maximum,delta.length)
o.data.update();bpy.context.view_layer.update()
report={'changed_vertices':changed,'max_displacement_mm':1000*maximum,'drivers':len(rig.animation_data.drivers),'hand_geometry_and_pose':'unchanged'}
(O/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_fretting_cuff_v446.blend'),compress=True)
print(json.dumps(report))
