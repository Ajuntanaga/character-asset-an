import bpy, json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[1]/'production_v362_face_anatomy'
scene=bpy.context.scene
saved=(scene.camera.location.copy(),scene.camera.rotation_euler.copy(),scene.camera.data.ortho_scale,scene.render.resolution_x,scene.render.resolution_y)
scene.camera.location=(0,-1.4,1.644)
scene.camera.rotation_euler=(Vector((0,0,1.644))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=.16
scene.render.resolution_x=800;scene.render.resolution_y=400
hidden=[]
for side in ('L','R'):
    obj=bpy.data.objects['V362_CORNEA.'+side];hidden.append((obj,obj.hide_render));obj.hide_render=True
scene.render.filepath=str(OUT/'v362_eye_without_cornea_close.png');bpy.ops.render.render(write_still=True)
dg=bpy.context.evaluated_depsgraph_get()
eye=bpy.data.objects['V362_EYE.L'].evaluated_get(dg)
mesh=eye.to_mesh()
(OUT/'eye_evaluated.json').write_text(json.dumps({'vertices':[list(v.co) for v in mesh.vertices],'polygons':[list(p.vertices) for p in mesh.polygons],'modifiers':[(m.name,m.type) for m in eye.modifiers]}))
eye.to_mesh_clear()
for obj,value in hidden:obj.hide_render=value
scene.camera.location,scene.camera.rotation_euler,scene.camera.data.ortho_scale,scene.render.resolution_x,scene.render.resolution_y=saved
print('Eye surface isolated; scene preview restored.')
