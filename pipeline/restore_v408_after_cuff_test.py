import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];o=bpy.data.objects['V357_CUFF_PATCH.R'];coords=json.loads((R/'production_v409_cuff_hem/vertices_before.json').read_text())
assert len(coords)==len(o.data.vertices)
for v,co in zip(o.data.vertices,coords):v.co=co
o.data.update();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'production_v408_clearance_margin/Character_An_clearance_margin_v408.blend'),compress=True)
print('Rejected cuff experiment restored; V408 hand pose retained')
