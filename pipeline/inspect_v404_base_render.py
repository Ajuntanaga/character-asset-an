import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=bpy.context.scene;o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];m=o.modifiers['Multires'];assert not bpy.app.is_job_running('RENDER')
old=(s.render.engine,s.render.filepath,m.show_render)
try:
 m.show_render=False;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
 s.render.filepath=str(R/'production_v404_hand_stack/base_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath,m.show_render=old
print('Base diagnostic complete; render settings restored')
