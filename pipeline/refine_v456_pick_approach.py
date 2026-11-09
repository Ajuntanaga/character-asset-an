import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v456_pick_approach';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];b=r.pose.bones['IK-Hand.R'];g=bpy.data.objects['V206_GUITAR_ROOT'];original=b.matrix.copy()
check=(root/'pipeline/check_v455_relaxed_picking.py').read_text();check=check[:check.index("(root/'production_v455")]
results=[]
for mm in (8,12,16,19):
 mat=original.copy();mat.translation+=r.matrix_world.inverted().to_3x3()@g.matrix_world.to_3x3()@Vector((0,0,-mm/1000));b.matrix=mat;r.update_tag();bpy.context.view_layer.update()
 scope={};exec(compile(check,'clearance','exec'),scope);result=scope['r'];result['translation_mm']=mm;results.append(result)
 if result['crossed_string_centrelines'] or result['sampled_clearance_m']<.0003:break
chosen=next((x['translation_mm'] for x in reversed(results) if not x['crossed_string_centrelines'] and x['sampled_clearance_m']>=.0003),0)
mat=original.copy();mat.translation+=r.matrix_world.inverted().to_3x3()@g.matrix_world.to_3x3()@Vector((0,0,-chosen/1000));b.matrix=mat;r.update_tag();bpy.context.view_layer.update()
(out/'report.json').write_text(json.dumps({'chosen_mm':chosen,'trials':results},indent=2));print(json.dumps({'chosen_mm':chosen,'trials':results}))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v456_pick_approach/v456_wrists.png','resolution':[1000,700],'samples':24,'scale':.9,'camera':[.25,-3.5,1.42],'target':[0,-.15,1.1]}))
p=root/'pipeline/render_preview_job.py';exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
