import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v504_distal_pad';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];p=bpy.data.objects['V361_NYLON_PICK'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted()
e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();coords=[gi@e.matrix_world@v.co for v in m.vertices];groups=[h.vertex_groups[max(v.groups,key=lambda w:w.weight).group].name for v in m.vertices];faces=[list(f.vertices) for f in m.polygons]
index=BVHTree.FromPolygons(coords,[f for f in faces if all('Finger_Index' in groups[i] for i in f)])
pairs=[]
for i,(c,n) in enumerate(zip(coords,groups)):
 if n!='DEF-Finger_Thumb3.R':continue
 q,norm,j,d=index.find_nearest(c)
 if d<.008:pairs.append({'thumb_vertex':i,'thumb':list(c),'index':list(q),'normal':list(norm),'gap':d})
pairs.sort(key=lambda v:v['gap'])
pairs.insert(0,{'thumb_vertex':5953,'thumb':list(coords[5953]),'index':list(coords[2036]),'normal':list((coords[5953]-coords[2036]).normalized()),'gap':(coords[5953]-coords[2036]).length})
report={'file':bpy.data.filepath,'drivers':len(r.animation_data.drivers),'pairs':pairs[:15],'pick_vertices':[list(gi@p.matrix_world@v.co) for v in p.data.vertices],'pick_faces':[list(f.vertices) for f in p.data.polygons],'pick_world':[list(row) for row in p.matrix_world],'wrist_world':[list(row) for row in r.matrix_world@r.pose.bones['IK-Hand.R'].matrix],'bones':{n:{'head':list(gi@r.matrix_world@r.pose.bones[n].head),'tail':list(gi@r.matrix_world@r.pose.bones[n].tail)} for n in ['DEF-Hand.R']+[f'DEF-Finger_{f}{i}.R' for f in ('Thumb','Index','Middle','Ring','Pinky') for i in (1,2,3)]},'hand_vertices':[list(c) for c in coords],'hand_groups':groups,'hand_faces':faces}
e.to_mesh_clear();(out/'frame.json').write_text(json.dumps(report));print(json.dumps({k:v for k,v in report.items() if k in ('file','drivers','pairs','bones')}))
