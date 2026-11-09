import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out=root/'production_v464_linear_deformation'
assert not bpy.app.is_job_running('RENDER')
for name,value in json.loads((out/'original_modifier.json').read_text()).items():
 for m in bpy.data.objects[name].modifiers:
  if m.type=='ARMATURE':m.use_deform_preserve_volume=value
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
for name,matrix in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[name].matrix_basis=Matrix(matrix)
r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
print('Restored playing pose and volume-preserving skinning; 1957 drivers intact')
