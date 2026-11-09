import bpy,json,math,itertools
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v509_loose_pick_pose'
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];bs=[rig.pose.bones[f'FK-Finger_Middle{i}.R'] for i in (1,2)]
base=[b.rotation_euler.x for b in bs];rows=[]
f=root/'pipeline/check_v458_grip_fit.py'
s=f.read_text().split("(root/'production_v458_grip_fit/check.json')")[0]
for delta in itertools.product((-20,-10,0,10,20),repeat=2):
 for b,x,d in zip(bs,base,delta):b.rotation_euler.x=x+math.radians(d)
 rig.update_tag();bpy.context.view_layer.update();env={'__file__':str(f)};exec(compile(s,str(f),'exec'),env)
 result=env['r'];rows.append(dict(delta=delta,**result))
good=[a for a in rows if not a['crossed_string_centrelines'] and a['sampled_clearance_m']>.0003]
best=min(good,key=lambda a:sum(d*d for d in a['delta'])) if good else None
for b,x,d in zip(bs,base,best['delta'] if best else (0,0)):b.rotation_euler.x=x+math.radians(d)
rig.update_tag();bpy.context.view_layer.update()
(out/'sweep.json').write_text(json.dumps({'rows':rows,'selected':best},indent=2));print(json.dumps({'passing':len(good),'selected':best}))
if best:
 p=root/'pipeline/render_preview_request.json';q=json.loads(p.read_text());q['output']='production_v509_loose_pick_pose/clear.png';p.write_text(json.dumps(q));f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f)})
