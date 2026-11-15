"""Compare original groom with finer dark fibers; keep saved checkpoint intact."""
import json
from pathlib import Path
import runpy
import bpy
import numpy as np

root = Path(__file__).resolve().parents[1]
record = json.loads((root / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
renderer = str(Path(__file__).with_name('render_v740_cloud_groom.py'))
settings = {'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': record,
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(record['size']),
            'SAMPLES': 48, 'DENOISE': True, 'ADAPTIVE_THRESHOLD': .035}
runpy.run_path(renderer, init_globals={**settings, 'TAG': 'v762_groom_before'})

material = bpy.data.materials.new('V762_DARK_FINE_HAIR_TRIAL')
material.use_nodes = True
nodes = material.node_tree.nodes
nodes.clear()
shader = nodes.new('ShaderNodeBsdfHairPrincipled')
shader.parametrization = 'MELANIN'
for name, value in {'Melanin': .99, 'Melanin Redness': .12, 'Roughness': .30,
                    'Radial Roughness': .38, 'Random Color': .025,
                    'Random Roughness': .08}.items():
    if name in shader.inputs:
        shader.inputs[name].default_value = value
output = nodes.new('ShaderNodeOutputMaterial')
material.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
changes = []
for name in ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT']:
    obj = bpy.data.objects[name]
    radii = obj.data.attributes['radius'].data
    values = np.empty(len(radii), dtype=np.float32)
    radii.foreach_get('value', values)
    before = [float(np.min(values)), float(np.median(values)), float(np.max(values))]
    values *= .75
    radii.foreach_set('value', values)
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj.data.update_tag()
    changes.append({'object': name, 'radius_before_min_median_max': before,
                    'radius_scale': .75, 'points': len(values)})
bpy.context.view_layer.update()
print(json.dumps({'stage': 'GROOM_REFINEMENT', 'changes': changes}), flush=True)
runpy.run_path(renderer, init_globals={**settings, 'TAG': 'v762_groom_after'})
(root / 'results/v762_groom_changes.json').write_text(json.dumps({
    'changes': changes, 'source_checkpoint_saved': False,
    'scope': 'Scalp fiber shading and radius trial only; no face or rig edits'
}, indent=2))
