"""Compare elliptical scalp-fiber shading without changing the accepted groom."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v776_mustache_density')
assert not head.get('v777_scalp_huang')
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + p for p in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V775_SCALP_UNDERCOAT']


def fingerprint(name):
    data = bpy.data.objects[name].data
    points = np.empty(len(data.position_data) * 3, np.float32)
    data.position_data.foreach_get('vector', points)
    uvs = np.empty(len(data.curves) * 2, np.float32)
    data.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs)
    radii = np.empty(len(points) // 3, np.float32)
    data.attributes['radius'].data.foreach_get('value', radii)
    counts = np.array([len(curve.points) for curve in data.curves], np.int32)
    return hashlib.sha256(b''.join(a.tobytes() for a in (points, uvs, radii, counts))).hexdigest()


before = {name: fingerprint(name) for name in grooms}
original = bpy.data.materials['V766_DARK_NATURAL_HAIR']
material = original.copy()
material.name = 'V777_ELLIPTICAL_SCALP_HAIR'
shader = next(node for node in material.node_tree.nodes
              if node.bl_idname == 'ShaderNodeBsdfHairPrincipled')
shader.model = 'HUANG'
assert shader.parametrization == 'MELANIN'
# Retain physical reflection/transmission factors; change the scattering model,
# cross-section and small strand-to-strand variation, not global light intensity.
changes = {'Aspect Ratio': .70, 'Roughness': .35, 'Random Color': .03,
           'Random Roughness': .15, 'Reflection': 1., 'Transmission': 1.,
           'Secondary Reflection': 1.}
for name, value in changes.items():
    shader.inputs[name].default_value = value
original_group = bpy.data.objects['V766_ASSET_SCALP'].modifiers['Follow native face and FACS'].node_group
scalp_group = original_group.copy()
scalp_group.name = 'V777_SCALP_HAIR_ATTACHMENT'
material_nodes = [node for node in scalp_group.nodes
                  if node.bl_idname == 'GeometryNodeSetMaterial']
assert len(material_nodes) == 1
assert not material_nodes[0].inputs['Material'].is_linked
material_nodes[0].inputs['Material'].default_value = material
for name in ('V766_ASSET_SCALP', 'V775_SCALP_UNDERCOAT'):
    obj = bpy.data.objects[name]
    materials = obj.data.materials
    assert len(materials) == 1 and materials[0] == original
    materials[0] = material
    modifier = obj.modifiers['Follow native face and FACS']
    assert modifier.node_group == original_group
    modifier.node_group = scalp_group
assert all(fingerprint(name) == before[name] for name in grooms)
assert all(bpy.data.objects[name].data.materials[0] == original
           for name in grooms if name not in ('V766_ASSET_SCALP', 'V775_SCALP_UNDERCOAT'))
assert all(bpy.data.objects[name].modifiers['Follow native face and FACS'].node_group == original_group
           for name in grooms if name not in ('V766_ASSET_SCALP', 'V775_SCALP_UNDERCOAT'))
assert next(node for node in original_group.nodes
            if node.bl_idname == 'GeometryNodeSetMaterial').inputs['Material'].default_value == original
head['v777_scalp_huang'] = True
report = {'source': bpy.data.filepath, 'model': 'HUANG', 'changes': changes,
          'all_groom_geometry_roots_and_uvs_unchanged': True,
          'facial_groom_materials_unchanged': True,
          'scalp_material_assignment': 'dedicated Geometry Nodes Set Material override and data slots',
          'face_shape_keys': 52, 'rig_drivers': 1957,
          'documentation': 'https://docs.blender.org/manual/en/5.0/render/shader_nodes/shader/hair_principled.html',
          'license': 'licenses/hair-asset-sources.md'}
(OUT / 'v777_scalp_huang.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V777_scalp_huang_trial.blend').resolve()), compress=True)

camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms,
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v777_hair', 'front', {}),
        ('v777_hair', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v777_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('SCALP_HUANG_TRIAL_COMPLETE', flush=True)
