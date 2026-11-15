"""Cloud-only neutral and turned neck views, retaining the full lower opening."""
from pathlib import Path
import runpy
import bpy

head = bpy.data.objects['V740_NATIVE_FACE']
assert head.parent_type == 'OBJECT'
assert any(m.type == 'ARMATURE' for m in head.modifiers)
renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
for label, degrees in [('rest', 0.), ('left', 25.), ('right', -25.)]:
    runpy.run_path(str(renderer), init_globals={
        'TAG': 'v755_neck_' + label,
        'VIEWS': ['front'], 'SAMPLES': 16,
        'HEAD_TURN_DEGREES': degrees,
        'CAMERA_TARGET': (0., -.015, 1.585), 'ORTHO_SCALE': .46,
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT'],
    })
