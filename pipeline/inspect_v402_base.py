import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];g=bpy.data.objects['V206_GUITAR_ROOT'];m=o.modifiers['Multires'];old=m.levels
try:
 m.levels=0;bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();p=[list(g.matrix_world.inverted()@e.matrix_world@v.co) for v in mesh.vertices];e.to_mesh_clear()
finally:m.levels=old;bpy.context.view_layer.update()
(R/'production_v402_pick_wrist/base_posed.json').write_text(json.dumps(p));print(len(p))
