"""Render true rest-shape silhouette with armature disabled temporarily."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER') and 'v495' in bpy.data.filepath
hand=bpy.data.objects['V357_ANATOMICAL_HAND.R'];mod=hand.modifiers[0];assert mod.type=='ARMATURE'
flags=(mod.show_viewport,mod.show_render)
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v496_rest_shape').replace("normal=(frame@Vector((1,0,0))).normalized()","normal=(hand.matrix_world.to_3x3()@Vector((0,-1,0))).normalized()")
try:
 mod.show_viewport=False;mod.show_render=False;bpy.context.view_layer.update()
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
finally:
 mod.show_viewport,mod.show_render=flags;bpy.context.view_layer.update()
print('Armature visibility restored; rest review only')
