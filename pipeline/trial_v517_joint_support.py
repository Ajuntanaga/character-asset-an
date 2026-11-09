"""Test subdivision support at dorsal finger joint arcs, preserving base mesh."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v517_joint_support';out.mkdir(exist_ok=True)
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert 'v514' in bpy.data.filepath and not bpy.app.is_job_running('RENDER')
assert h.data.attributes.get('crease_edge') is None
names=[f'FK-Finger_{f}{i}.R' for f in ('Index','Middle','Ring','Pinky') for i in (1,2,3)]
pose={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
assert not (out/'original.json').exists()
(out/'original.json').write_text(json.dumps({n:[list(row) for row in m] for n,m in pose.items()}))
w=[{h.vertex_groups[g.group].name:g.weight for g in v.groups} for v in h.data.vertices]
attr=h.data.attributes.new('crease_edge','FLOAT','EDGE');changed=[]
try:
 for finger in ('Index','Middle','Ring','Pinky'):
  for joint in (2,3):
   a=f'DEF-Finger_{finger}{joint-1}.R';b=f'DEF-Finger_{finger}{joint}.R'
   ring={i for i,ww in enumerate(w) if ww.get(a,0)>.05 and ww.get(b,0)>.05}
   if not ring:continue
   cy=sum(h.data.vertices[i].co.y for i in ring)/len(ring)
   for edge in h.data.edges:
    if all(i in ring for i in edge.vertices):
     y=sum(h.data.vertices[i].co.y for i in edge.vertices)/2
     if y<cy:
      attr.data[edge.index].value=.55;changed.append(edge.index)
 def render(label):
  h.data.update();h.update_tag();rig.update_tag();bpy.context.view_layer.update()
  f=root/'pipeline/review_v492_isolated_palm.py'
  code=f.read_text().replace('production_v492_palm_review','production_v517_joint_support/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
  exec(compile(code,str(f),'exec'),{'__file__':str(f)})
 render('playing')
 for n in names:rig.pose.bones[n].rotation_euler.x=0
 render('open')
 (out/'changes.json').write_text(json.dumps({'edges':changed,'crease':.55}))
finally:
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 h.data.attributes.remove(attr);h.data.update();h.update_tag();rig.update_tag();bpy.context.view_layer.update()
 assert len(rig.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957}))
print('V517 dorsal joint support comparison complete',len(changed))
