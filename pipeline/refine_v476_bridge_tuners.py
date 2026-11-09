"""Add individually modelled axial tuner barrels from the supplied front photo."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v476_guitar_review';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert not bpy.data.objects.get('V476_TUNER_S1')
g=bpy.data.objects['V206_GUITAR_ROOT'];mat=bpy.data.materials['V356_BLACK_HARDWARE'];backup={}
for i in range(1,9):
 o=bpy.data.objects[f'V206_BRIDGE_S{i}'];backup[o.name]={'scale':list(o.scale),'location':list(o.location)}
 x,y,z=o.location
 # Keep saddle and string endpoint fixed; shorten the old block behind it.
 o.scale.x*=.72;o.location.x-=.006
 rings=[(.009,.0034),(.013,.0034),(.014,.0041),(.032,.0041),(.033,.0037)]
 vs=[];n=96
 for dx,rad in rings:
  for k in range(n):
   a=2*math.pi*k/n
   rr=rad-(.00022 if dx>=.014 and k%3==1 else 0)
   vs.append((x+dx,y+rr*math.cos(a),z+rr*math.sin(a)))
 faces=[tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
 for j in range(len(rings)-1):
  for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 mesh=bpy.data.meshes.new(f'V476_TUNER_S{i}');mesh.from_pydata(vs,[],faces);mesh.update()
 ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.parent=g;ob.matrix_parent_inverse=Matrix.Identity(4);mesh.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
 bevel=ob.modifiers.new('Machined rim','BEVEL');bevel.width=.00018;bevel.segments=2
 bevel.limit_method='ANGLE'
 ob['reference']='references/props/strandberg/strandberg_full_product.jpg'
(out/'bridge_backup.json').write_text(json.dumps(backup,indent=2))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v476_guitar_review/tuners.png','resolution':[900,700],'samples':32,'scale':.27,'camera':list(g.matrix_world@Vector((.88,.18,.35))),'target':list(g.matrix_world@Vector((.735,0,.015)))}))
p=root/'pipeline/render_preview_job.py';exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
