"""Retain the licensed groom; compare a repaired atlas on unchanged face geometry."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
keys = {key.name: float(key.value) for key in head.data.shape_keys.key_blocks}
assert len(keys) == 52 and len(rig.animation_data.drivers) == 1957
installed = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
assert all(name in bpy.data.objects for name in installed)
old_names = ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']
report = {'source_scene': bpy.data.filepath, 'removed_superseded_grooms': [],
          'shape_keys': len(keys), 'rig_drivers': len(rig.animation_data.drivers),
          'geometry_and_neutral_expression_changed': False}

# The original full checkpoint is retained in its GitHub release. Remove only
# its four explicitly superseded, hidden grooms from this new working copy.
for name in old_names:
    obj = bpy.data.objects[name]
    assert obj.hide_render, ('Superseded groom unexpectedly visible', name)
    report['removed_superseded_grooms'].append(name)
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
baseline = OUT / 'V766_active_licensed_hair.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(baseline.resolve()), compress=True)
report['baseline_bytes'] = baseline.stat().st_size

atlas_path = ROOT.parent / 'github_assets/v767/repaired_face_albedo.png'
if atlas_path.exists():
    atlas = bpy.data.images.load(str(atlas_path.resolve()), check_existing=False)
    atlas.colorspace_settings.name = 'sRGB'
    atlas.pack()
    matched = []
    for material in head.data.materials:
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if (node.type == 'TEX_IMAGE' and node.image and
                        Path(node.image.filepath).name == 'Character_An_photoreal_head_basecolor_v326.png'):
                    node.image = atlas
                    matched.append([material.name, node.name])
    assert matched, 'No source skin atlas nodes matched'
    report['repaired_atlas'] = {'sha256': hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
                                'size': list(atlas.size), 'image_nodes': matched}
    camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    base = {'EXTRA_OBJECTS': installed, 'EXCLUDE_OBJECTS': old_names,
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **base, 'TAG': 'v767_repaired_albedo', 'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera})
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **base, 'TAG': 'v767_repaired_albedo_front', 'VIEWS': ['front']})
    assert {key.name: float(key.value) for key in head.data.shape_keys.key_blocks} == keys
    assert len(rig.animation_data.drivers) == 1957
    trial = OUT / 'V767_repaired_albedo_trial.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(trial.resolve()), compress=True)
    report['trial_bytes'] = trial.stat().st_size

(OUT / 'v767_albedo_trial.json').write_text(json.dumps(report, indent=2))
print('ALBEDO_TRIAL_COMPLETE', json.dumps(report), flush=True)
