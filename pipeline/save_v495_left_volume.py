"""Retain visually reviewed left linear-skinning candidate separately."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v495_left_volume'
assert not bpy.app.is_job_running('RENDER') and 'v494' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
hand=bpy.data.objects['V357_ANATOMICAL_HAND.L']
assert [m.type for m in hand.modifiers]==['ARMATURE','MULTIRES']
mod=hand.modifiers[0];assert mod.use_deform_preserve_volume
path=out/'Character_An_left_linear_skinning_v495.blend';assert not path.exists()
mod.use_deform_preserve_volume=False;bpy.context.view_layer.update()
ev=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
assert all(math.isfinite(x) for v in mesh.vertices for x in v.co)
count=len(mesh.vertices);ev.to_mesh_clear()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
(out/'saved.json').write_text(json.dumps({'file':bpy.data.filepath,'vertices':count,'drivers':len(rig.animation_data.drivers),'left_preserve_volume':mod.use_deform_preserve_volume,'right_preserve_volume':bpy.data.objects['V357_ANATOMICAL_HAND.R'].modifiers[0].use_deform_preserve_volume},indent=2))
print('V495 saved')
