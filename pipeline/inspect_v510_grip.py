import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v510_grip_review';out.mkdir(exist_ok=True)
f=root/'pipeline/inspect_v503_pick_frame.py';exec(compile(f.read_text().replace('production_v503_pick_seating','production_v510_grip_review'),str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v510_grip_review')
s=s.replace("points=[obj.matrix_world@v.co for v in mesh.vertices]", "pick=bpy.data.objects['V361_NYLON_PICK']; pickcopy=bpy.data.objects.new('V510_PICK_REVIEW',pick.data.copy());scene.collection.objects.link(pickcopy);pickcopy.matrix_world=pick.matrix_world;pickcopy.color=(.05,.08,.12,1)\npoints=[obj.matrix_world@v.co for v in mesh.vertices]")
s=s.replace("scene.display.shading.color_type='SINGLE'", "scene.display.shading.color_type='OBJECT';obj.color=(.58,.44,.31,1)")
s=s.replace("camdata.ortho_scale=.38", "camdata.ortho_scale=.20")
s=s.replace("bpy.context.window.scene=scene", "center=(rig.matrix_world@rig.pose.bones['DEF-Finger_Thumb3.R'].head+rig.matrix_world@rig.pose.bones['DEF-Finger_Index3.R'].head)*.5\nbpy.context.window.scene=scene")
s=s.replace("[('across_a',normal),('across_b',-normal)]", "[('dorsal',normal),('palmar',-normal),('side',(frame@Vector((0,0,1))).normalized())]")
s=s.replace("bpy.data.meshes.remove(mesh);", "pickmesh=pickcopy.data;bpy.data.objects.remove(pickcopy,do_unlink=True);bpy.data.meshes.remove(pickmesh)\n bpy.data.meshes.remove(mesh);")
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
