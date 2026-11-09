import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v417_join_smooth';O.mkdir(exist_ok=True);s=bpy.context.scene;o=bpy.data.objects['V416_SHARED_BOUNDARY_CUFF.R']
assert not bpy.app.is_job_running('RENDER')
mod=o.modifiers.new('Tailored sleeve smoothing','SUBSURF');mod.levels=1;mod.render_levels=2
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_join_smooth_v417.blend'),compress=True)
engine,path,scale=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v417_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path;s.camera.data.ortho_scale=scale
print('V417 saved')
