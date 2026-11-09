import bpy,bmesh
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=bpy.context.scene;o=bpy.data.objects['V416_SHARED_BOUNDARY_CUFF.R']
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'production_v416_shared_join/Character_An_shared_join_v416.blend'),compress=True)
engine,path,scale=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(R/'production_v416_shared_join/v416_normals_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path;s.camera.data.ortho_scale=scale
print('Normals recalculated')
