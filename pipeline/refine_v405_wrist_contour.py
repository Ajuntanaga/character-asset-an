import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v405_wrist_contour';O.mkdir(exist_ok=True)
s=bpy.context.scene;assert not bpy.app.is_job_running('RENDER');o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];backup=[]
for v in o.data.vertices:
 x,y,z=v.co
 if x>=-.008 or z<=-.02 or z>=.095:continue
 t=max(0,min(1,(z+.02)/.055));t=t*t*(3-2*t)
 u=max(0,min(1,(.095-z)/.025));u=u*u*(3-2*u)
 backup.append([v.index,list(v.co)]);v.co.x+=( -.008-x)*t*u*.85
# Keep all topology, finger weights, drivers and the previous file intact.
o.data.update();o.update_tag();bpy.context.view_layer.update();(O/'vertices_before.json').write_text(json.dumps(backup))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_wrist_contour_v405.blend'),compress=True)
old=(s.render.engine,s.render.filepath)
try:
 s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v405_contour_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath=old
print(json.dumps({'edited_vertices':len(backup)}))
