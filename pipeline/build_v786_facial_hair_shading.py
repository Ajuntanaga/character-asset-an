"""Compare darker facial-hair highlights without changing the accepted groom."""
import hashlib
import json
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(globals().get('OUT', ROOT / 'results'))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = globals().get('RENDER', True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v784_crown_mix') and not head.get('v785_eye_aperture')
assert not head.get('v786_facial_hair_shading')
assert len(head.data.shape_keys.key_blocks) == 52 and len(rig.animation_data.drivers) == 1957
targets = ['V766_ASSET_' + part for part in ('BROWS', 'BEARD', 'MUSTACHE')]
grooms = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V775_SCALP_UNDERCOAT', 'V779_TEMPLE_HAIR']


def fingerprint(name):
    data = bpy.data.objects[name].data
    digest = hashlib.sha256()
    for collection, prop, width in [(data.position_data, 'vector', 3),
                                   (data.attributes['radius'].data, 'value', 1),
                                   (data.attributes['surface_uv_coordinate'].data, 'vector', 2)]:
        values = np.empty(len(collection) * width, np.float32)
        collection.foreach_get(prop, values)
        digest.update(values.tobytes())
    return digest.hexdigest()


before = {name: fingerprint(name) for name in grooms}
unchanged = {name: (tuple(bpy.data.objects[name].data.materials),
                   bpy.data.objects[name].modifiers['Follow native face and FACS'].node_group)
             for name in grooms if name not in targets}
source = bpy.data.objects[targets[0]].data.materials[0]
assert all(bpy.data.objects[name].data.materials[0] == source for name in targets)
material = source.copy()
material.name = 'V786_FACIAL_HAIR_REDUCED_REFLECTION'
shader = next(node for node in material.node_tree.nodes
              if node.bl_idname == 'ShaderNodeBsdfHairPrincipled')
assert shader.model == 'CHIANG' and shader.parametrization == 'MELANIN'
shader.model = 'HUANG'
shader.inputs['Reflection'].default_value = .4
for name in targets:
    obj = bpy.data.objects[name]
    modifier = obj.modifiers['Follow native face and FACS']
    group = modifier.node_group.copy()
    group.name = 'V786_' + name.removeprefix('V766_ASSET_') + '_ATTACHMENT'
    assignments = [node for node in group.nodes if node.bl_idname == 'GeometryNodeSetMaterial']
    assert len(assignments) == 1 and not assignments[0].inputs['Material'].is_linked
    assignments[0].inputs['Material'].default_value = material
    obj.data.materials[0] = material
    modifier.node_group = group
assert all(fingerprint(name) == before[name] for name in grooms)
for name, (materials, group) in unchanged.items():
    obj = bpy.data.objects[name]
    assert tuple(obj.data.materials) == materials
    assert obj.modifiers['Follow native face and FACS'].node_group == group
head['v786_facial_hair_shading'] = True
bpy.context.view_layer.update()
report = {'source': bpy.data.filepath, 'targets': targets, 'model_before': 'CHIANG',
          'model_after': 'HUANG', 'reflection': .4, 'melanin': float(shader.inputs['Melanin'].default_value),
          'all_seven_groom_geometry_uvs_radii_unchanged': True,
          'other_four_groom_materials_and_groups_unchanged': True,
          'face_shape_keys': 52, 'rig_drivers': 1957,
          'license': 'licenses/hair-asset-sources.md',
          'checkpoint': str((OUT / 'V786_facial_hair_shading_trial.blend').resolve())}
(OUT / 'v786_facial_hair_shading.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=report['checkpoint'], compress=True)
if RENDER:
    camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    for view in ['front', 'reference_orientation']:
        tag = 'v786_facial_hair_' + view
        runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
            'EXTRA_OBJECTS': grooms,
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True,
            'CAMERA_RECORD': camera if view == 'reference_orientation' else {},
            'TAG': tag, 'VIEWS': [view]})
        rendered = json.loads((ROOT / 'results' / (tag + '_render_report.json')).read_text())
        assert rendered['production_unchanged'] and rendered['head_basis_restored']
        assert rendered['rig_drivers'] == 1957
print('FACIAL_HAIR_SHADING_COMPLETE', json.dumps(report), flush=True)
