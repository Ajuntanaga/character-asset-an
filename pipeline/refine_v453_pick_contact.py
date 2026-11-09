import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v453_pick_contact';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];c=r.pose.bones['IK-Hand.R'];original=c.matrix.copy();g=bpy.data.objects['V206_GUITAR_ROOT'];p=bpy.data.objects['V361_NYLON_PICK']
gi=g.matrix_world.inverted();pv=[p.matrix_world@v.co for v in p.data.vertices];tip=min(pv,key=lambda v:(gi@v).z);tl=gi@tip
segments=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale())
 for sp in o.data.splines:
  pts=[o.matrix_world@v.co.xyz for v in sp.points]
  segments.extend((i,a,b,rad) for a,b in zip(pts,pts[1:]))
# Target nearest point on fourth string at current longitudinal pick position.
candidates=[]
for i,a,b,rad in segments:
 if i!=4:continue
 al=gi@a;bl=gi@b
 if min(al.x,bl.x)<=tl.x<=max(al.x,bl.x):
  t=(tl.x-al.x)/(bl.x-al.x);target=a.lerp(b,t)+g.matrix_world.to_3x3()@Vector((0,0,rad+.0007));break
else:raise RuntimeError('No target')
axis=(g.matrix_world.to_3x3()@Vector((1,0,0))).normalized();trials=[];chosen=None
for angle in (20,-20,35,-35,50,-50,65,-65,80,-80):
 transform=Matrix.Translation(target)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-tip)
 c.matrix=r.matrix_world.inverted()@transform@r.matrix_world@original;r.update_tag();bpy.context.view_layer.update()
 e=bpy.data.objects['V357_ANATOMICAL_HAND.R'].evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(f.vertices) for f in m.polygons]);e.to_mesh_clear()
 hits=[];margin=1
 for i,a,b,rad in segments:
  d=b-a
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
  n=max(1,math.ceil(d.length/.001))
  for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(b,k/n))[3]-rad-.00025)
 trials.append({'angle':angle,'crossings':sorted(set(hits)),'margin':margin})
 if not hits and margin>.0003:chosen=angle;break
if chosen is None:c.matrix=original;r.update_tag();bpy.context.view_layer.update()
report={'chosen':chosen,'trials':trials,'original_tip':list(tip),'target':list(target),'translation':(target-tip).length,'drivers':len(r.animation_data.drivers)}
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if chosen is not None:
 request={'output':'production_v453_pick_contact/v453_wrists.png','resolution':[1000,700],'samples':24,'scale':.9,'camera':[.25,-3.5,1.42],'target':[0,-.15,1.1]}
 (root/'pipeline/render_preview_request.json').write_text(json.dumps(request));exec(compile((root/'pipeline/render_preview_job.py').read_text(),str(root/'pipeline/render_preview_job.py'),'exec'))
