"""Compare central palm depth while preserving wrist, thumb and finger roots."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'production_v512_palm_depth';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v508' in bpy.data.filepath
hand=bpy.data.objects['V357_ANATOMICAL_HAND.R']
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
original=[v.co.copy() for v in hand.data.vertices]
p=out/'original_coordinates.json';assert not p.exists();p.write_text(json.dumps([list(v) for v in original]))
mod=next(m for m in hand.modifiers if m.type=='ARMATURE');flags=(mod.show_viewport,mod.show_render)
f=root/'pipeline/review_v492_isolated_palm.py'
def render(label,rest):
 mod.show_viewport=not rest;mod.show_render=not rest;bpy.context.view_layer.update()
 s=f.read_text().replace('production_v492_palm_review','production_v512_palm_depth/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
 if rest:s=s.replace('normal=(frame@Vector((1,0,0))).normalized()','normal=(hand.matrix_world.to_3x3()@Vector((0,-1,0))).normalized()')
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
try:
 render('baseline_rest',True)
 changes=[]
 for v in hand.data.vertices:
  co=v.co.copy();t=(-co.z-.018)/.087
  if not 0<t<1:continue
  thumb=sum(g.weight for g in v.groups if 'Thumb' in hand.vertex_groups[g.group].name)
  influence=math.sin(math.pi*t)**2*(1-min(1,thumb))
  # Flatten depth around the central metacarpal plane; blend to wrist/MCP.
  delta=-(co.y-.002)*.25*influence
  v.co.y+=delta
  if abs(delta)>1e-7:changes.append(abs(delta))
 hand.data.update();hand.update_tag()
 (out/'candidate_coordinates.json').write_text(json.dumps([list(v.co) for v in hand.data.vertices]))
 render('trial_rest',True);render('trial_curl',False)
 assert len(rig.animation_data.drivers)==1957
 (out/'report.json').write_text(json.dumps({'changed':len(changes),'max_mm':max(changes)*1000,'drivers':1957}))
finally:
 for v,co in zip(hand.data.vertices,original):v.co=co
 hand.data.update();hand.update_tag();mod.show_viewport,mod.show_render=flags;bpy.context.view_layer.update()
 (out/'restored.json').write_text(json.dumps({'restored':all((v.co-co).length<1e-7 for v,co in zip(hand.data.vertices,original)),'drivers':len(rig.animation_data.drivers)}))
print('V512 comparison complete; original geometry restored')
