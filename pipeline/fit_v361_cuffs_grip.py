"""Fit the existing cuffs and lower the picking grip, preserving V360."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');OUT=ROOT/'production_v361_pick_cuffs';OUT.mkdir(exist_ok=True)
s=bpy.context.scene;r=next(o for o in s.objects if o.name.endswith('_CLOUDRIG_CONTROLS'));g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted()
report={'cuffs':{}}
if not s.get('v361_cuffs_fitted'):
 for side,sign in (('L',1),('R',-1)):
  o=next(o for o in s.objects if o.name.endswith('_CUFF_PATCH.'+side));original=o.data;o.data=original.copy();o.data.name='V361_Fitted_Cuff.'+side
  bm=bmesh.new();bm.from_mesh(o.data)
  todo=set(bm.verts);components=[]
  while todo:
   queue=[todo.pop()];component=[]
   while queue:
    v=queue.pop();component.append(v)
    for e in v.link_edges:
     other=e.other_vert(v)
     if other in todo:todo.remove(other);queue.append(other)
   components.append(component)
  components.sort(key=len,reverse=True);remove=[v for comp in components[1:] for v in comp]
  if len(remove)>len(components[0])*.15:raise RuntimeError('Unexpected disconnected cuff topology')
  bmesh.ops.delete(bm,geom=remove,context='VERTS')
  for v in bm.verts:
   t=max(0,min(1,(v.co.z-.895)/.050));t=t*t*(3-2*t)
   sx=.59+.41*t;sy=.57+.43*t
   v.co.x=sign*(.298+.004*t)+(v.co.x-sign*.302)*sx
   v.co.y=.014-.006*t+(v.co.y-.008)*sy
  bm.to_mesh(o.data);bm.free();o.data.update()
  report['cuffs'][side]={'disconnected_artifact_vertices_removed':len(remove),'retained_vertices':len(o.data.vertices),'original_mesh':original.name}
 s['v361_cuffs_fitted']=True
sol=json.loads((ROOT/'production_v360_hand_clearance/picking_solution.json').read_text());h=Matrix(sol['hand_matrix_guitar']);h[2][3]-=.027
r.pose.bones['IK-Hand.R'].matrix=r.matrix_world.inverted()@g.matrix_world@h
r.update_tag();bpy.context.view_layer.update()
o=next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.R'));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();T=gi@ev.matrix_world
coords=[T@v.co for v in mesh.vertices];groups=[]
for v in mesh.vertices:
 dom=max(v.groups,key=lambda e:e.weight);groups.append(o.vertex_groups[dom.group].name)
faces=[list(p.vertices) for p in mesh.polygons if all('Finger_Index' in groups[i] for i in p.vertices)]
bvh=BVHTree.FromPolygons(coords,faces,all_triangles=False)
contacts=[]
for v,p,name in zip(mesh.vertices,coords,groups):
 if name!='DEF-Finger_Thumb3.R':continue
 nearest,normal,index,distance=bvh.find_nearest(p)
 if distance is not None and distance<.008:
  contacts.append({'point':list(p),'index_point':list(nearest),'normal':list(normal),'signed_mm':(p-nearest).dot(normal)*1000})
report['thumb_index']={'near_samples':len(contacts),'minimum_signed_mm':min(c['signed_mm'] for c in contacts),'contacts':contacts}
report['hand_matrix_guitar']=list(map(list,h))
report['right_surface']={'vertices':[list(p) for p in coords],'faces':[list(p.vertices) for p in mesh.polygons],'groups':groups}
ev.to_mesh_clear()
(OUT/'fit_report.json').write_text(json.dumps(report))
s.render.engine='BLENDER_WORKBENCH';s.render.threads_mode='FIXED';s.render.threads=1;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100;cam=s.camera;cam.data.type='ORTHO'
for label,pos,target,scale in (('fretting_cuff',(.285,.025,.6),(.285,.025,0),.32),('picking_front',(.68,-.06,.6),(.68,-.06,0),.32),('picking_side',(.68,.40,.20),(.68,-.04,.04),.30)):
 cam.location=g.matrix_world@Vector(pos);q=g.matrix_world@Vector(target);cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 s.render.filepath=str(OUT/f'v361_{label}.png');bpy.ops.render.render(write_still=True)
print(json.dumps({'cuffs':report['cuffs'],'thumb_index_minimum_signed_mm':report['thumb_index']['minimum_signed_mm'],'contact_samples':len(contacts)}))
