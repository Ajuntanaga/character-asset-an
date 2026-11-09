import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v494_left_deform'
assert not bpy.app.is_job_running('RENDER') and 'v493' in bpy.data.filepath
hand=bpy.data.objects['V357_ANATOMICAL_HAND.L'];rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert [m.type for m in hand.modifiers]==['MULTIRES','ARMATURE']
p=out/'Character_An_bilateral_deform_order_v494.blend';assert not p.exists()
hand.modifiers.move(1,0);bpy.context.view_layer.update()
checks=[]
for side in ('L','R'):
 obj=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 assert [m.type for m in obj.modifiers]==['ARMATURE','MULTIRES']
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 finite=all(math.isfinite(x) for v in mesh.vertices for x in v.co);assert finite
 checks.append({'side':side,'vertices':len(mesh.vertices),'finite':finite});ev.to_mesh_clear()
assert len(rig.animation_data.drivers)==1957
bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'status.json').write_text(json.dumps({'file':str(p),'hands':checks,'drivers':1957,'change':'Both hand meshes deform before Multires','limits':['Fretting contacts unresolved','Anatomy still too smooth','No animation-wide acceptance']},indent=2))
print(str(p))
