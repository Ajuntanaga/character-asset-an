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
    ('smile_half', {'Smile.L': .4, 'Smile.R': .4}),
    ('smile', {'Smile.L': .8, 'Smile.R': .8}),
    ('pucker', {'MouthPucker': .8}),
    ('turn_left', {}),
    ('turn_right_jaw', {'JawOpen': .35}),
]
records = []
try:
    for label, expression in cases:
        pose = dict.fromkeys(properties, 0.)
        pose.update(expression)
        tag = 'v740_expression_' + label
        # Frontal silhouettes hide lip projection and oral clearance.
        views = ['front', 'profile'] if label in {'jaw', 'pucker'} else ['front']
        if label in {'smile_half', 'smile'}:
            views.append('three_quarter')
        runpy.run_path(str(renderer), init_globals={
            'POSE': pose, 'TAG': tag, 'VIEWS': views, 'SAMPLES': 24,
            'HEAD_TURN_DEGREES': {'turn_left': 25., 'turn_right_jaw': -25.}.get(label, 0.),
        })
        records.append({'expression': expression, 'image': tag + '_front.png',
                        'images': [tag + '_' + view + '.png' for view in views]})
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
             'Includes static FK head turns; continuous motion, body motion and textured skin remain untested.',
}, indent=2))
