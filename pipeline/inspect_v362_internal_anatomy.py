import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'production_v362_face_anatomy'
source=ROOT/'third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
if not bpy.data.objects.get('V362_SOURCE_Jaw'):
    with bpy.data.libraries.load(str(source),link=False) as (a,b):
        names=[n for n in a.objects if 'jaw' in n.lower()];b.objects=names
    for obj in b.objects:
        if obj and obj.type=='MESH':obj.name='V362_SOURCE_Jaw'
report={'jaw':[]}
for o in bpy.data.objects:
    if o.name.startswith('V362_SOURCE_Jaw'):
        report['jaw'].append({'name':o.name,'verts':len(o.data.vertices),'faces':len(o.data.polygons),'bounds':list(map(list,o.bound_box)),'matrix':list(map(list,o.matrix_world)),'groups':[g.name for g in o.vertex_groups],'materials':[m.name for m in o.data.materials],'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons]})
o=bpy.data.objects['V362_EYE.L']
report['eye']={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons]}
(OUT/'internal_anatomy_geometry.json').write_text(json.dumps(report))
print(json.dumps({'jaw':[{k:v for k,v in j.items() if k not in ['vertices','polygons']} for j in report['jaw']],'eye_vertices':len(o.data.vertices)}))
