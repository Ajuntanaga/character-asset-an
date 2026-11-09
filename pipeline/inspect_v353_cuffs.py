import bpy
import json
import numpy as np
from pathlib import Path

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v353_cuff_repair'
out.mkdir(exist_ok=True)
scene = bpy.data.scenes['V352_CLOUDRIG_HANDS']
for window in bpy.context.window_manager.windows:
    window.scene = scene
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
scene.frame_set(1)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
body = scene.objects['V352_TRIPO_CHARACTER_BODY_BOUND']
rig = scene.objects['V352_CLOUDRIG_CONTROLS']
report = {'file': bpy.data.filepath, 'body_matrix': [list(r) for r in body.matrix_world],
          'objects': [o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render],
          'sections': {}, 'hands': {}, 'bones': {}}
vertices = np.array([body.matrix_world @ v.co for v in body.data.vertices])
for side, sign in [('L', 1), ('R', -1)]:
    sections = []
    for z in np.arange(.89, 1.001, .01):
        section = vertices[(sign * vertices[:, 0] > .255) &
                           (abs(vertices[:, 2] - z) < .003)]
        if len(section):
            sections.append({'z': round(z, 3), 'count': len(section),
                             'min': section.min(axis=0).tolist(),
                             'max': section.max(axis=0).tolist(),
                             'median': np.median(section, axis=0).tolist()})
    report['sections'][side] = sections
    hand = scene.objects['V352_ANATOMICAL_HAND.' + side]
    points = np.array([hand.matrix_world @ v.co for v in hand.data.vertices])
    report['hands'][side] = {'min': points.min(axis=0).tolist(),
                            'max': points.max(axis=0).tolist()}
    for name in ['DEF-Hand.' + side, 'DEF-Forearm.' + side, 'DEF-Forearm1.' + side]:
        bone = rig.data.bones.get(name)
        if bone:
            report['bones'][name] = {'head': list(bone.head_local), 'tail': list(bone.tail_local)}
(out / 'cuff_inspection.json').write_text(json.dumps(report, indent=2))
result = report
