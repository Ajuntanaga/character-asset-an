"""Export eyelid boundary deformation and evaluated driver values; no scene save."""
import json
from pathlib import Path
from collections import Counter
import bpy

head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
control = rig.pose.bones['Head']
keys = head.data.shape_keys.key_blocks
# Only polygon boundary vertices: loose donor eye vertices are not eyelids.
edges = Counter(tuple(sorted(edge)) for p in head.data.polygons for edge in p.edge_keys)
boundary = sorted({v for edge, count in edges.items() if count == 1 for v in edge})
ids = [i for i in boundary if 1.625 < keys['Basis'].data[i].co.z < 1.665
       and .012 < abs(keys['Basis'].data[i].co.x) < .065]
assert len(ids) >= 20, 'Expected native eye opening boundaries'
props = ['Blink.L', 'Blink.R']
saved = {p: control[p] for p in props}
records = []
try:
    for value in [0., .5, 1.]:
        for p in props:
            control[p] = value
        rig.update_tag(refresh={'OBJECT'})
        bpy.context.view_layer.update()
        records.append({'requested_blink': value,
                        'evaluated_key_values': {n: keys[n].value for n in
                                                 ['eyeBlinkLeft', 'eyeBlinkRight']}})
finally:
    for p, value in saved.items():
        control[p] = value
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
report = {
    'object': head.name, 'boundary_vertex_ids': ids,
    'coordinates_local': {name: [list(keys[name].data[i].co) for i in ids]
                          for name in ['Basis', 'eyeBlinkLeft', 'eyeBlinkRight']},
    'driver_samples': records,
    'drivers': [{'path': d.data_path, 'valid': d.is_valid,
                 'expression': d.driver.expression} for d in head.data.shape_keys.animation_data.drivers
                if 'eyeBlink' in d.data_path],
    'scope': 'Control evaluation and raw eyelid boundary coordinates; not a closure or render acceptance test.'}
Path('results').mkdir(exist_ok=True)
Path('results/blink_boundary_diagnostic.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'boundary_vertices': len(ids), 'driver_samples': records}))
