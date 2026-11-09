import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from pipeline.guitar_geometry import GuitarGeometry,load_authoritative_mapping
out=root/'production_v469_fretting';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];inv=g.matrix_world.inverted();geo=GuitarGeometry.from_mapping(load_authoritative_mapping())
h=bpy.data.objects['V357_ANATOMICAL_HAND.L'];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();tree=BVHTree.FromPolygons([inv@e.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);e.to_mesh_clear()
rows=[]
for digit,string,fret,hover in [('Index','S6',11,0),('Middle','S6',10,.01),('Ring','S7',9,0),('Pinky','S8',11,0)]:
 p=geo.local_pad_from_neutral(string,fret);target=Vector((.260+p[0],p[1],.02045));tail=inv@r.matrix_world@r.pose.bones[f'DEF-Finger_{digit}3.L'].tail
 near=tree.find_nearest(target)
 rows.append(dict(digit=digit,string=string,fret=fret,target=list(target),bone_tail=list(tail),bone_error_mm=(tail-target-Vector((0,0,.006+hover))).length*1000,nearest_hand_mm=near[3]*1000,nearest_hand=list(near[0])))
(out/'initial.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
req={'output':'production_v469_fretting/before.png','resolution':[900,700],'samples':24,'scale':.30,'camera':list(g.matrix_world@Vector((.35,.28,.38))),'target':list(g.matrix_world@Vector((.35,.01,.035)))}
(root/'pipeline/render_preview_request.json').write_text(json.dumps(req));f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
