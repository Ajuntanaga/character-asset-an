"""Measure real, world-space hand motion and render bounded diagnostic views."""
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v354_rig_driver_repair'
scene = bpy.data.scenes['V354_CLOUDRIG_DRIVERS']
rig = scene.objects['V354_CLOUDRIG_CONTROLS']
properties = rig.pose.bones['Properties']
camera = scene.camera
camera_state = camera.matrix_world.copy(), camera.data.type, camera.data.ortho_scale
frame = scene.frame_current
arm_state = {key: properties[key] for key in ('ik_left_arm', 'ik_right_arm')}
controls = {side: rig.pose.bones['FK-Hand.' + side] for side in ('L', 'R')}
control_state = {side: (bone.rotation_mode, bone.matrix_basis.copy())
                 for side, bone in controls.items()}
render_keys = ('engine', 'threads_mode', 'threads', 'resolution_x',
               'resolution_y', 'resolution_percentage', 'filepath')
render_state = {key: getattr(scene.render, key) for key in render_keys}
image_format = scene.render.image_settings.file_format


def update():
    rig.update_tag()
    bpy.context.view_layer.update()


def positions(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        values = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', values)
        matrix = np.asarray(evaluated.matrix_world, dtype=np.float64)
        return values.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    finally:
        evaluated.to_mesh_clear()


def motion(before, after):
    if before.shape != after.shape or not np.isfinite(after).all():
        raise RuntimeError('Invalid evaluated hand coordinates')
    displacement = np.linalg.norm(after - before, axis=1)
    return {'maximum_vertex_displacement_mm': float(displacement.max()) * 1000,
            'mean_vertex_displacement_mm': float(displacement.mean()) * 1000,
            'moving_vertices': int(np.count_nonzero(displacement > .001))}


def render(side, label):
    sign = 1 if side == 'L' else -1
    camera.location = (sign * 1.2, -.18, .875)
    target = Vector((sign * .30, .01, .85))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(out / f'v354_hand_{side}_{label}.png')
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


report = {'driver_count': len(rig.animation_data.drivers), 'hands': {},
          'units': 'World-space millimetres',
          'limits': 'Workbench geometry diagnostics; does not prove skin quality or guitar contact.'}
try:
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 1
    scene.render.resolution_x, scene.render.resolution_y = 700, 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'TEXTURE'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'BOTH'
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .245
    scene.frame_set(1)
    update()
    rest = {}
    for side in controls:
        rest[side] = positions(scene.objects['V354_ANATOMICAL_HAND.' + side])
        report['hands'][side] = {'open_image': render(side, 'open')}
    scene.frame_set(24)
    update()
    for side in controls:
        result = motion(rest[side], positions(scene.objects['V354_ANATOMICAL_HAND.' + side]))
        if not 5 < result['maximum_vertex_displacement_mm'] < 160:
            raise RuntimeError(f'{side}: finger action did not produce bounded motion: {result}')
        result['image'] = render(side, 'curl')
        report['hands'][side]['finger_curl'] = result
    scene.frame_set(1)
    for key in arm_state:
        properties[key] = 0.0
    update()
    for side, control in controls.items():
        hand = scene.objects['V354_ANATOMICAL_HAND.' + side]
        before = positions(hand)
        before_tail = rig.matrix_world @ rig.pose.bones['DEF-Hand.' + side].tail
        sign = 1 if side == 'L' else -1
        control.rotation_mode = 'XYZ'
        control.rotation_euler = (.35, .20 * sign, .12 * sign)
        update()
        result = motion(before, positions(hand))
        after_tail = rig.matrix_world @ rig.pose.bones['DEF-Hand.' + side].tail
        result['def_hand_tail_displacement_mm'] = (after_tail - before_tail).length * 1000
        if not 5 < result['maximum_vertex_displacement_mm'] < 150:
            raise RuntimeError(f'{side}: wrist did not produce bounded hand motion: {result}')
        if result['def_hand_tail_displacement_mm'] < 5:
            raise RuntimeError(f'{side}: FK wrist did not drive DEF-Hand: {result}')
        result['control'] = control.name
        result['arm_mode'] = 'FK'
        result['rotation_radians'] = list(control.rotation_euler)
        result['image'] = render(side, 'wrist')
        report['hands'][side]['wrist_bend'] = result
        control.rotation_mode, control.matrix_basis = control_state[side]
        update()
finally:
    for side, control in controls.items():
        control.rotation_mode, control.matrix_basis = control_state[side]
    for key, value in arm_state.items():
        properties[key] = value
    camera.matrix_world, camera.data.type, camera.data.ortho_scale = camera_state
    for key, value in render_state.items():
        setattr(scene.render, key, value)
    scene.render.image_settings.file_format = image_format
    scene.frame_set(frame)
    update()

(out / 'hand_deformation_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
