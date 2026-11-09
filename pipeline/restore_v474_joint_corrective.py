import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v474_joint_study'
assert not bpy.app.is_job_running('RENDER')
assert not (out/'restored.json').exists()
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 assert set(k.name for k in o.data.shape_keys.key_blocks)=={'Basis','V474_Middle_MCP_flex','V474_Ring_MCP_flex','V474_Pinky_MCP_flex'}
 o.shape_key_clear()
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
for n,m in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[n].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
report={'restored':True,'drivers':1957,'reason':'Rendered local 3mm pose-driven dorsal compression insufficient to correct broad knuckle shape; no production save.'}
(out/'restored.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
