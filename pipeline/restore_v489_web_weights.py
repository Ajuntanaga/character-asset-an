import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v489_web_weights'
assert not bpy.app.is_job_running('RENDER')
o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];weights=json.loads((out/'original_weights.json').read_text())
for i,w in enumerate(weights):
 for g in o.vertex_groups:g.remove([i])
 for name,value in w.items():o.vertex_groups[name].add([i],value,'REPLACE')
o.data.update()
f=root/'pipeline/restore_v488_pick_curl.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
error=max(abs(g.weight-weights[v.index][o.vertex_groups[g.group].name]) for v in o.data.vertices for g in v.groups)
assert error<1e-6
(out/'restored.json').write_text(json.dumps({'weights_max_error':error,'restored':True,'drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)}))
print('V489 weights restored',error)
