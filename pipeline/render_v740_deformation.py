"""Render bounded expression checks on the isolated groom checkpoint, remotely."""
from pathlib import Path
import json
import runpy
import bpy

rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
control = rig.pose.bones['Head']
properties = ['JawOpen', 'Blink.L', 'Blink.R', 'BrowInnerUp',
              'BrowDown.L', 'BrowDown.R', 'BrowOuterUp.L', 'BrowOuterUp.R',
              'Smile.L', 'Smile.R', 'MouthPucker']
assert all(prop in control for prop in properties)
original = {prop: control[prop] for prop in properties}
renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
cases = [
    ('rest', {}),
    ('jaw', {'JawOpen': .55}),
    ('blink', {'Blink.L': 1., 'Blink.R': 1.}),
    ('brow_raise', {'BrowInnerUp': .7, 'BrowOuterUp.L': .6, 'BrowOuterUp.R': .6}),
]
records = []
try:
    for label, expression in cases:
        pose = dict.fromkeys(properties, 0.)
        pose.update(expression)
        tag = 'v740_expression_' + label
        runpy.run_path(str(renderer), init_globals={
            'POSE': pose, 'TAG': tag, 'VIEWS': ['front'], 'SAMPLES': 24,
        })
        records.append({'expression': expression, 'image': tag + '_front.png'})
finally:
    for prop, value in original.items():
        control[prop] = value
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
assert all(control[prop] == value for prop, value in original.items())
Path('results/deformation_render_report.json').write_text(json.dumps({
    'cases': records,
    'restored_controls': original,
    'scope': 'Expression images for visual review; no automatic deformation acceptance. '
             'Head turns, body motion and textured skin remain untested.',
}, indent=2))
