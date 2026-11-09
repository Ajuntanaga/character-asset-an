"""Render reversible open/curl hand studies without clearing animation drivers."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
out=root/'production_v440_hand_folds'/'deformation_review'
out.mkdir(exist_ok=True)
scene=bpy.context.scene
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
bones=[rig.pose.bones[f'FK-Finger_{digit}{joint}.L'] for digit in ('Index','Middle','Ring','Pinky') for joint in (1,2,3)]
original={b.name:(b.rotation_mode, b.rotation_euler.copy(),b.rotation_quaternion.copy()) for b in bones}
old_engine=scene.render.engine
old_path=scene.render.filepath
old_res=(scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage)
sh=scene.display.shading
old_sh=(sh.light,sh.color_type,sh.show_shadows,sh.show_cavity)
results=[]
try:
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=700; scene.render.resolution_y=700; scene.render.resolution_percentage=100
    sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True
    for name,angles in [('open',(0,0,0)),('curl',(45,80,40))]:
        for b in bones:
            joint=int(b.name.split('.')[0][-1])
            b.rotation_mode='XYZ';b.rotation_euler=(math.radians(angles[joint-1]),0,0)
        rig.update_tag();bpy.context.view_layer.update()
        obj=bpy.data.objects['V357_ANATOMICAL_HAND.L'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=obj.to_mesh()
        coords=[obj.matrix_world@v.co for v in mesh.vertices]
        finite=all(math.isfinite(c) for v in coords for c in v)
        results.append({'pose':name,'vertices':len(coords),'finite':finite,'drivers':len(rig.animation_data.drivers),'bounds_m':[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]})
        obj.to_mesh_clear()
        scene.render.filepath=str(out/f'{name}.png')
        bpy.ops.render.render(write_still=True)
finally:
    for b in bones:
        mode,euler,quat=original[b.name];b.rotation_mode=mode;b.rotation_euler=euler;b.rotation_quaternion=quat
    rig.update_tag();bpy.context.view_layer.update()
    scene.render.engine=old_engine;scene.render.filepath=old_path
    scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=old_res
    sh.light,sh.color_type,sh.show_shadows,sh.show_cavity=old_sh
(out/'report.json').write_text(json.dumps({'poses':results,'original_pose_restored':True,'scope':'Left four fingers only; images require visual review, not guitar contact validation'},indent=2))
print(json.dumps(results))
