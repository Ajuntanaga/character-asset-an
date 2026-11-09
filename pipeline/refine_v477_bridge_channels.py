"""Reversible channel housings; retain the existing saddle/string endpoints."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v477_bridge_channels';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert not bpy.data.objects.get('V477_Base_S1')
g=bpy.data.objects['V206_GUITAR_ROOT'];black=bpy.data.materials['V356_BLACK_HARDWARE'];steel=bpy.data.materials['V356_NICKEL_FRETS'];backup={}
def meshob(name,vs,fs,mat,bevel=0):
 m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(o);o.parent=g;o.matrix_parent_inverse=Matrix.Identity(4);m.materials.append(mat)
 if bevel:
  b=o.modifiers.new('Machined edges','BEVEL');b.width=bevel;b.segments=3
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def box(name,lo,hi):
 vs=[(x,y,z) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
 return meshob(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],black,.00045)
for i in range(1,9):
 old=bpy.data.objects[f'V206_BRIDGE_S{i}'];backup[old.name]={'hide_render':old.hide_render,'hide_set':old.hide_get()};old.hide_render=True;old.hide_set(True)
 saddle=bpy.data.objects[f'V206_SADDLE_S{i}'];x,y,z=saddle.location
 box(f'V477_Base_S{i}',(x-.006,y-.0042,.011),(x+.024,y+.0042,.015))
 for side in (-1,1):
  cy=y+side*.00355
  box(f'V477_Rail_{side}_S{i}',(x-.006,cy-.00065,.014),(x+.024,cy+.00065,.029))
 box(f'V477_End_S{i}',(x+.021,y-.0035,.014),(x+.024,y+.0035,.027))
 # Recessed recessed socket fastener inside the open channel.
 vs=[];n=24
 for radius,height in ((.0021,.015),(.0021,.018),(.001,.018),(.001,.0165)):
  for k in range(n):
   a=2*math.pi*k/n;vs.append((x+.011+radius*math.cos(a),y+radius*math.sin(a),height))
 fs=[]
 for j in range(3):
  for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 fs.append(tuple(range(3*n,4*n)))
 meshob(f'V477_Adjuster_S{i}',vs,fs,steel,.0001)
(out/'backup.json').write_text(json.dumps(backup,indent=2))
assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v477_bridge_channels/bridge.png','resolution':[900,700],'samples':32,'scale':.27,'camera':list(g.matrix_world@Vector((.88,.18,.35))),'target':list(g.matrix_world@Vector((.735,0,.015)))}))
p=root/'pipeline/render_preview_job.py';exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
