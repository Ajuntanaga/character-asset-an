"""Isolated short-edge smile-delta correction; never saves the source scene."""
from pathlib import Path
import json
import runpy
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parent
out = Path('results')
out.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
keys = head.data.shape_keys.key_blocks
basis = keys['Basis']
hotspots = [Vector((-.02760, -.10724, 1.57101)),
            Vector((.03080, -.10724, 1.57101))]
settings = {'TEXTURE_PATH': 'Character_An_photoreal_head_basecolor_v326.png',
            'VIEWS': ['front', 'three_quarter_reference_side'], 'SAMPLES': 16,
            'POSE': {'Smile.L': .8, 'Smile.R': .8}}
saved = {}
changes = []
try:
    runpy.run_path(str(root / 'render_v740_cloud_groom.py'),
                   init_globals={**settings, 'TAG': 'v743_smile_control'})
    for name in ('mouthSmileLeft', 'mouthSmileRight'):
        key = keys[name]
        assert key.relative_key == basis
        delta = [v.co - b.co for v, b in zip(key.data, basis.data)]
        groups = []
        for edge in head.data.edges:
            a, b = edge.vertices
            mid = (basis.data[a].co + basis.data[b].co) * .5
            if min((mid - p).length for p in hotspots) > .004:
                continue
            if (basis.data[a].co - basis.data[b].co).length >= .0001:
                continue
            if (delta[a] - delta[b]).length <= .0002:
                continue
            merged = {a, b}
            keep = []
            for group in groups:
                if group & merged:
                    merged |= group
                else:
                    keep.append(group)
            groups = keep + [merged]
        for group in groups:
            mean = sum((delta[i] for i in group), Vector()) / len(group)
            for i in sorted(group):
                correction = mean - delta[i]
                assert correction.length < .0003, 'Correction exceeds localized trial bound'
                saved[name, i] = key.data[i].co.copy()
                key.data[i].co = basis.data[i].co + mean
                changes.append({'key': name, 'vertex': i,
                                'correction_mm': correction.length * 1000})
    assert changes, 'No expected short-edge displacement discontinuities found'
    head.data.update()
    runpy.run_path(str(root / 'diagnose_v740_smile.py'))
    (out / 'smile_surface_diagnostic.json').rename(out / 'v743_smile_surface_diagnostic.json')
    runpy.run_path(str(root / 'render_v740_cloud_groom.py'),
                   init_globals={**settings, 'TAG': 'v743_smile_corrected'})
finally:
    for (name, i), co in saved.items():
        keys[name].data[i].co = co
    head.data.update()
    (out / 'v743_smile_trial.json').write_text(json.dumps({
        'status': 'TRIAL_REQUIRES_DEFORMATION_AND_RENDER_REVIEW',
        'changes': changes, 'source_coordinates_restored': all(
            (keys[name].data[i].co - co).length == 0 for (name, i), co in saved.items()),
        'scope': 'Only smile deltas on sub-0.1mm edges near mouth corners; basis and topology unchanged'
    }, indent=2))
