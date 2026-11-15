"""Reversible skin-color trial measured from the emission-only cheek render."""
import json
import runpy
from pathlib import Path
import bpy

root = Path(__file__).resolve().parent
head = bpy.data.objects['V740_NATIVE_FACE']
material = head.data.materials[0].copy()
material.name = 'V756_CHEEK_CALIBRATED_SKIN'
head.data.materials[0] = material
shader = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
mix = shader.inputs['Base Color'].links[0].from_node
assert mix.type == 'MIX_RGB'
assert mix.inputs[0].links[0].from_node.attribute_name == 'V740_CleanSkinBlend'
ramp = mix.inputs[2].links[0].from_node
assert ramp.type == 'VALTORGB' and len(ramp.color_ramp.elements) == 2
before = [list(e.color) for e in ramp.color_ramp.elements]
# Median RGB samples of two observed cheek patches from Standard, exposure-zero,
# emission-only output. Convert sRGB to scene-linear before averaging.
patches = [(180/255, 119/255, 83/255), (177/255, 116/255, 80/255)]
def linear(c):
    return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4
center = [sum(linear(p[i]) for p in patches)/2 for i in range(3)]
for element, scale in zip(ramp.color_ramp.elements, (.92, 1.08)):
    element.color = (*[c*scale for c in center], 1)
report = {'status': 'COLOR_TRIAL_NOT_ACCEPTED',
          'source_run': '43662774454', 'source_image': 'v740_unlit_basecolor_front.png',
          'sample_boxes_xyxy': [[150,350,180,385], [330,350,360,385]],
          'sample_medians_srgb': patches, 'center_linear': center,
          'before': before, 'after': [list(e.color) for e in ramp.color_ramp.elements],
          'scope': 'Procedural skin ramp only; cleanup weights, facial atlas and rig retained.'}
Path('results/v756_skin_calibration.json').write_text(json.dumps(report, indent=2)+'\n')
if not globals().get("MATERIAL_ONLY", False):
    bpy.ops.wm.save_as_mainfile(filepath=str(Path('results/V756_skin_calibration_trial.blend').resolve()))
    runpy.run_path(str(root/'render_v740_albedo.py'))
    runpy.run_path(str(root/'render_v740_cloud_groom.py'), init_globals={
        'TEXTURE_PATH': 'Character_An_photoreal_head_basecolor_v326.png',
        'TAG': 'v756_skin_calibration', 'VIEWS': ['front'], 'SAMPLES': 32})
