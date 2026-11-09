"""Place both hands around the guitar through the existing CloudRig controls."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v357_playing_pose'
OUT.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = next(o for o in scene.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
guitar = bpy.data.objects['V206_GUITAR_ROOT']
props = rig.pose.bones['Properties']
if rig.animation_data:
    rig.animation_data.action = None
scene.frame_set(1)

def update():
    rig.update_tag()
    bpy.context.view_layer.update()

def basis(forward, normal):
    normal = Vector(normal).normalized()
    forward = Vector(forward)
    forward = (forward - normal * forward.dot(normal)).normalized()
    return Matrix((normal.cross(forward), forward, normal)).transposed()

report = {'hands': {}, 'driver_count': len(rig.animation_data.drivers)}
for side, sign in (('L', 1), ('R', -1)):
    props['ik_left_arm' if side == 'L' else 'ik_right_arm'] = 1.0
    for digit in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb'):
        for i in range(1, 4):
            bone = rig.pose.bones[f'FK-Finger_{digit}{i}.{side}']
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = (0, 0, 0)
    hand = rig.data.bones['IK-Hand.' + side]
    middle = rig.data.bones['FK-Finger_Middle1.' + side]
    source = basis(middle.head_local - hand.head_local, (-sign, 0, 0))
    if side == 'L':
        wrist = Vector((.300, .120, -.075))
        target = basis((0, -.65, .76), (0, -.76, -.65))
        pole = Vector((.58, -.12, .98))
        curl = (35, 55, 30)
    else:
        wrist = Vector((.710, -.150, .055))
        target = basis((-.35, .937, 0), (0, 0, -1))
        pole = Vector((-.60, -.09, 1.04))
        curl = (30, 45, 30)
    rotation = guitar.matrix_world.to_3x3() @ target @ source.transposed()
    desired = (rotation @ hand.matrix_local.to_3x3()).to_4x4()
    desired.translation = guitar.matrix_world @ wrist
    rig.pose.bones['IK-Hand.' + side].matrix = rig.matrix_world.inverted() @ desired
    update()
    control = rig.pose.bones['POLE-Arm.' + side]
    matrix = control.matrix.copy()
    matrix.translation = rig.matrix_world.inverted() @ pole
    control.matrix = matrix
    for digit in ('Index', 'Middle', 'Ring', 'Pinky'):
        for i, angle in enumerate(curl, 1):
            rig.pose.bones[f'FK-Finger_{digit}{i}.{side}'].rotation_euler.x = math.radians(angle)
    update()
    actual = rig.matrix_world @ rig.pose.bones['DEF-Hand.' + side].matrix
    report['hands'][side] = {
        'wrist_target': list(desired.translation),
        'wrist_actual': list(actual.translation),
        'wrist_error_mm': (desired.translation - actual.translation).length * 1000,
        'hand_matrix_guitar': [list(row) for row in guitar.matrix_world.inverted() @ actual],
        'elbow_world': list(rig.matrix_world @ rig.pose.bones['IK-M-Forearm.' + side].head),
        'tips_guitar': {d: list(guitar.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones[f'DEF-Finger_{d}3.{side}'].tail)
                        for d in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')},
    }

for obj in scene.objects:
    if obj.name.startswith('V356_'):
        obj.name = obj.name.replace('V356_', 'V357_', 1)
scene.name = 'V357_PLAYING_POSE'
scene['quality_status'] = 'Initial controlled playing pose; contact solve and visual review pending'
camera = scene.camera
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x, scene.render.resolution_y = 1000, 1000
scene.render.resolution_percentage = 100
camera.data.type = 'ORTHO'
for label, position, target, scale in (
    ('arms_front', (.10, -4, 1.10), (.10, -.05, 1.10), 1.25),
    ('fretting_front', guitar.matrix_world @ Vector((.29, .02, .60)),
     guitar.matrix_world @ Vector((.29, .02, 0)), .35),
    ('fretting_side', guitar.matrix_world @ Vector((.29, .55, .35)),
     guitar.matrix_world @ Vector((.29, .02, 0)), .36),
):
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    scene.render.filepath = str(OUT / f'v357_{label}.png')
    bpy.ops.render.render(write_still=True)
(OUT / 'initial_arm_pose.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'Character_An_playing_pose_v357.blend'), compress=True)
print(json.dumps(report))
