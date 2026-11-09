import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v458_grip_fit'
assert not bpy.app.is_job_running('RENDER')
p=bpy.data.objects['V361_NYLON_PICK'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted();t=gi@p.matrix_world
n=(t.to_3x3()@p.data.polygons[0].normal).normalized();q=t@p.data.polygons[0].center-n*.00035
center=(Vector((.6352676749,-.0210620649,.0488677472))+Vector((.6344376802,-.0210691001,.048683133)))*.5
normal=Vector((.969659388,.148511946,.194177076)).normalized()
anchor=center-n*(center-q).dot(n)
xf=Matrix.Translation(center)@n.rotation_difference(normal).to_matrix().to_4x4()@Matrix.Translation(-anchor)
p.matrix_world=g.matrix_world@xf@gi@p.matrix_world;bpy.context.view_layer.update()
(out/'pick_alignment.json').write_text(json.dumps({'grip_center':list(center),'normal':list(normal),'old_plane_offset_mm':(center-q).dot(n)*1000,'transform':[list(row) for row in xf]},indent=2))
cam=g.matrix_world@Vector((.68,.28,.42));target=g.matrix_world@Vector((.635,-.02,.045))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v458_grip_fit/v458_pick_close.png','resolution':[720,640],'samples':24,'scale':.23,'camera':list(cam),'target':list(target)}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
