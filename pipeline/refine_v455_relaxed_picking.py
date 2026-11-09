import bpy,json,math
from pathlib import Path
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out=root/'production_v455_relaxed_picking';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
report={}
for finger,angles in [('Middle',(10,15,8)),('Ring',(15,20,10)),('Pinky',(20,25,12))]:
 for i,a in enumerate(angles,1):
  b=r.pose.bones[f'FK-Finger_{finger}{i}.R'];report[b.name]=list(b.rotation_euler);b.rotation_euler.x=math.radians(a)
r.update_tag();bpy.context.view_layer.update()
(out/'original_rotations.json').write_text(json.dumps(report))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v455_relaxed_picking/v455_wrists.png','resolution':[1000,700],'samples':24,'scale':.9,'camera':[.25,-3.5,1.42],'target':[0,-.15,1.1]}))
p=root/'pipeline/render_preview_job.py'
exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
