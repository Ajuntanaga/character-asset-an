import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v501_pick_refit';assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];b=r.pose.bones['IK-Hand.R'];p=bpy.data.objects['V361_NYLON_PICK'];g=bpy.data.objects['V206_GUITAR_ROOT'];backup=json.loads((out/'wrist_pick_original.json').read_text());bpy.context.view_layer.update()
xf=(r.matrix_world@b.matrix)@Matrix(backup['wrist_world']).inverted();p.matrix_world=xf@Matrix(backup['pick_world']);bpy.context.view_layer.update();t=g.matrix_world.inverted()@p.matrix_world
print('PICK_Z_RANGE',min((t@v.co).z for v in p.data.vertices),max((t@v.co).z for v in p.data.vertices))
q=json.loads((root/'pipeline/render_preview_request.json').read_text());q['output']='production_v501_pick_refit/corrected.png';(root/'pipeline/render_preview_request.json').write_text(json.dumps(q));f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f)})
