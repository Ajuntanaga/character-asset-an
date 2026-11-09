import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v504_distal_pad';r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER')
for name,mat in json.loads((out/'original.json').read_text())['index'].items():r.pose.bones[name].matrix_basis=Matrix(mat)
for name,mat in json.loads((out/'thumb_original.json').read_text()).items():r.pose.bones[name].matrix_basis=Matrix(mat)
bpy.context.view_layer.update()
bpy.data.objects['V361_NYLON_PICK'].matrix_world=Matrix(json.loads((root/'production_v503_pick_seating/frame.json').read_text())['pick_world']);bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
print('Restored V501 index, thumb and pick')
