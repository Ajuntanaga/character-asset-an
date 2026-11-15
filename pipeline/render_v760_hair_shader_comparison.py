"""Isolate broad gray hair highlights without changing groom geometry."""
from pathlib import Path
import json
import runpy
import bpy

material = bpy.data.materials['V740_BLACK_RINGLET_FIBERS']
shader = next(n for n in material.node_tree.nodes if n.type == 'BSDF_HAIR_PRINCIPLED')
original = {name: shader.inputs[name].default_value
            for name in ('Roughness', 'Radial Roughness')}
trials = []
try:
    for label, roughness, radial in [('baseline', original['Roughness'], original['Radial Roughness']),
                                      ('narrow', .28, .28)]:
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Radial Roughness'].default_value = radial
        runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
                      init_globals={'TAG': 'v760_' + label,
                                    'VIEWS': ['reference_orientation'],
                                    'RESOLUTION': (2048, 2560),
                                    'BORDER': (.375, .625, .65, .85),
                                    'SAMPLES': 64, 'ADAPTIVE_THRESHOLD': .02,
                                    'DENOISE': False, 'PRESERVE_MATERIALS': True})
        trials.append({'label': label, 'roughness': roughness, 'radial_roughness': radial})
finally:
    for name, value in original.items():
        shader.inputs[name].default_value = value
Path('results/v760_shader_comparison.json').write_text(json.dumps(
    {'trials': trials, 'geometry_changed': False, 'checkpoint_saved': False}, indent=2))
