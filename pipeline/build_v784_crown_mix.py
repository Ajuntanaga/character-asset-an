"""Retain primary crown curls and introduce a minority of finer donor paths."""
import json
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(globals().get('OUT', ROOT / 'results'))
APPLY = globals().get('APPLY', True)
RENDER = globals().get('RENDER', True)
# Construct the reviewed V783 alternative without mutating the V782 scene.
trial = runpy.run_path(str(ROOT / 'pipeline/build_v783_crown_subclumps.py'),
                       init_globals={'OUT': OUT, 'APPLY': False, 'RENDER': False})
head, rig, obj = trial['head'], trial['rig'], trial['obj']
data, old = obj.data, trial['old']
assert not head.get('v784_crown_mix')
mixed = old.copy()
mixed[2::3] = trial['updated'][2::3]
assert np.array_equal(mixed[:, :2], old[:, :2])
assert np.array_equal(mixed[0::3], old[0::3])
assert np.array_equal(mixed[1::3], old[1::3])
assert np.isfinite(mixed).all()
other_grooms = trial['other_grooms']
other_materials = {name: list(bpy.data.objects[name].data.materials) for name in other_grooms}
other_groups = {name: bpy.data.objects[name].modifiers['Follow native face and FACS'].node_group
                for name in other_grooms}
material = data.materials[0]
shader = next(node for node in material.node_tree.nodes
              if node.bl_idname == 'ShaderNodeBsdfHairPrincipled')
assert shader.model == 'HUANG' and shader.parametrization == 'MELANIN'
assert abs(shader.inputs['Reflection'].default_value - 1.) < 1e-6
report = {'source': bpy.data.filepath, 'applied': bool(APPLY),
          'outer_curves': len(data.curves), 'primary_siblings_retained': '2 of 3',
          'changed_strands': int(np.count_nonzero(np.linalg.norm(mixed-old, axis=2).max(axis=1) > 1e-7)),
          'max_displacement_m': float(np.linalg.norm(mixed-old, axis=2).max()),
          'roots_first_segments_uvs_radii_unchanged': True,
          'other_six_grooms_unchanged': True,
          'outer_crown_reflection_trial': {'before': 1., 'after': .4},
          'face_shape_keys': 52, 'rig_drivers': 1957,
          'license': 'licenses/hair-asset-sources.md'}


def render(tag, **options):
    camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
        'EXTRA_OBJECTS': [obj.name]+other_grooms,
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True,
        'CAMERA_RECORD': camera, 'TAG': tag, 'VIEWS': ['reference_orientation'], **options})
    rendered = json.loads((ROOT / 'results' / (tag+'_render_report.json')).read_text())
    assert rendered['production_unchanged'] and rendered['head_basis_restored']
    assert rendered['rig_drivers'] == 1957


if APPLY:
    data.position_data.foreach_set('vector', mixed.ravel())
    data.update_tag()
    if RENDER:
        render('v784_mix_original_highlights')
    # Dedicated material and modifier group isolate the comparison to the outer crown.
    material = material.copy()
    material.name = 'V784_CROWN_REDUCED_REFLECTION'
    shader = next(node for node in material.node_tree.nodes
                  if node.bl_idname == 'ShaderNodeBsdfHairPrincipled')
    shader.inputs['Reflection'].default_value = .4
    group = trial['attachment'].copy()
    group.name = 'V784_CROWN_HAIR_ATTACHMENT'
    assignments = [node for node in group.nodes if node.bl_idname == 'GeometryNodeSetMaterial']
    assert len(assignments) == 1 and not assignments[0].inputs['Material'].is_linked
    assignments[0].inputs['Material'].default_value = material
    data.materials[0] = material
    obj.modifiers['Follow native face and FACS'].node_group = group
    obj['v784_adaptation'] = 'Retain two primary siblings; one alternative donor sibling. Outer crown reflection factor 0.4.'
    head['v784_crown_mix'] = True
assert all(trial['fingerprint'](name) == trial['before'][name] for name in other_grooms)
assert all(list(bpy.data.objects[name].data.materials) == other_materials[name] for name in other_grooms)
assert all(bpy.data.objects[name].modifiers['Follow native face and FACS'].node_group == other_groups[name]
           for name in other_grooms)
assert np.array_equal(trial['values'](data.attributes['surface_uv_coordinate'], 'vector', 2), trial['uvs'])
assert np.array_equal(trial['values'](data.attributes['radius'], 'value'), trial['radii'])
assert len(head.data.shape_keys.key_blocks) == 52 and len(rig.animation_data.drivers) == 1957
(OUT / 'v784_crown_mix.json').write_text(json.dumps(report, indent=2)+'\n')
if APPLY:
    bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V784_crown_mix_trial.blend').resolve()), compress=True)
    if RENDER:
        render('v784_mix_reduced_highlights')
        render('v784_motion', HEAD_TURN_DEGREES=12., POSE={'Blink.L': .65, 'Blink.R': .65})
print('CROWN_MIX_COMPLETE', json.dumps(report), flush=True)
