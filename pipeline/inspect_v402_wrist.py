import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'production_v402_pick_wrist';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
s=bpy.context.scene;g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted();out={}
for o in s.objects:
 if o.type=='MESH' and (o.name.endswith('_ANATOMICAL_HAND.R') or o.name=='V361_NYLON_PICK'):
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
  out[o.name]={'rest':[list(v.co) for v in o.data.vertices],'world_rest':[list(o.matrix_world@v.co) for v in o.data.vertices],'posed':[list(gi@e.matrix_world@v.co) for v in m.vertices],'faces':[list(p.vertices) for p in m.polygons],'weights':[[[o.vertex_groups[w.group].name,w.weight] for w in v.groups] for v in o.data.vertices],'modifiers':[(x.name,x.type) for x in o.modifiers]};e.to_mesh_clear()
(O/'before.json').write_text(json.dumps(out));print([(k,len(v['rest']),len(v['posed']),v['modifiers']) for k,v in out.items()])
