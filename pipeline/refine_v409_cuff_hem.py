import bpy,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v409_cuff_hem';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
o=bpy.data.objects['V357_CUFF_PATCH.R'];m=o.data;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];s=bpy.context.scene
(O/'vertices_before.json').write_text(json.dumps([list(v.co) for v in m.vertices]))
counts=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in m.polygons for i in range(len(p.vertices)))
boundary={v for edge,n in counts.items() if n==1 for v in edge};rim={i for i in boundary if m.vertices[i].co.z<.92};top=boundary-rim
assert len(rim)==220 and len(top)==310
adj=collections.defaultdict(set)
for a,b in counts:adj[a].add(b);adj[b].add(a)
# Blend the boundary correction through eight edge rings, leaving the upper join fixed.
target=sum(m.vertices[i].co.z for i in rim)/len(rim);distance={i:0 for i in rim};queue=collections.deque(rim)
while queue:
 i=queue.popleft()
 if distance[i]>=8:continue
 for j in adj[i]:
  if j not in distance and j not in top:distance[j]=distance[i]+1;queue.append(j)
delta={i:target-m.vertices[i].co.z for i in rim}
for depth in range(1,9):
 for i,d in distance.items():
  if d==depth:
   near=[j for j in adj[i] if distance.get(j,99)<depth];delta[i]=sum(delta[j] for j in near)/len(near)
for i,d in distance.items():m.vertices[i].co.z+=delta[i]*(1-d/9)**2
m.update();bpy.context.view_layer.update();assert len(r.animation_data.drivers)==1957
(O/'report.json').write_text(json.dumps({'rim_vertices':len(rim),'changed_vertices':len(distance),'target_z':target,'max_displacement_m':max(abs(delta[i]*(1-d/9)**2) for i,d in distance.items()),'drivers':1957},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_cuff_hem_v409.blend'),compress=True)
old=(s.render.engine,s.render.filepath)
try:s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v409_pick_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath=old
