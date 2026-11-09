import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v404_hand_stack';O.mkdir(exist_ok=True)
s=bpy.context.scene;assert not bpy.app.is_job_running('RENDER');o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
for row in json.loads((R/'production_v403_wrist_blend/weights_before.json').read_text()):
 i=row['vertex']
 for name in ['DEF-Hand.R','DEF-Forearm_2.R']:o.vertex_groups[name].remove([i])
 for name,w in row['weights']:o.vertex_groups[name].add([i],w,'REPLACE')
report={}
for side in ['L','R']:
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];report[side]={'before':[(m.name,m.type) for m in o.modifiers]}
 with bpy.context.temp_override(object=o,active_object=o):bpy.ops.object.modifier_move_up(modifier='Multires')
 report[side]['after']=[(m.name,m.type) for m in o.modifiers]
bpy.context.view_layer.update();(O/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_hand_stack_v404.blend'),compress=True)
q=json.loads((R/'pipeline/render_preview_request.json').read_text());q['output']='production_v404_hand_stack/v404_pick_close.png';(R/'pipeline/render_preview_request.json').write_text(json.dumps(q))
exec(compile((R/'pipeline/render_preview_job.py').read_text(),str(R/'pipeline/render_preview_job.py'),'exec'))
print(json.dumps(report))
