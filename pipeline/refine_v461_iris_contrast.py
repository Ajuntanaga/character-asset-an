import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v461_iris_contrast';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v460' in bpy.data.filepath
old=bpy.data.materials['V374_PROCEDURAL_BROWN_EYE.001'];m=old.copy();m.name='V461_Brown_Iris';g=next(n for n in m.node_tree.nodes if n.type=='GROUP');g.node_tree=g.node_tree.copy()
changes={'Iris Primary':(.105,.044,.015,1),'Iris Dark Gaps':(.019,.008,.003,1),'Limbus Primary':(.025,.012,.005,1),'Limbus Secondary':(.012,.005,.002,1)}
before={k:list(g.inputs[k].default_value) for k in changes}
for k,v in changes.items():g.inputs[k].default_value=v
for side in ('L','R'):
 o=bpy.data.objects['V374_EYE.'+side]
 for slot in o.material_slots:
  if slot.material==old:slot.material=m
(out/'report.json').write_text(json.dumps({'before':before,'after':changes},indent=2))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v461_iris_contrast/v461_face.png','resolution':[700,800],'samples':32,'scale':.46,'camera':[.1,-2,1.67],'target':[0,0,1.65]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
