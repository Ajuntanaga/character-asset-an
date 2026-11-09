"""Exercise the active FK wrist path and render the resulting deformation."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v353_cuff_repair'
scene = bpy.data.scenes['V353_CLOUDRIG_CUFFS']
rig = scene.objects['V353_CLOUDRIG_CONTROLS']
properties = rig.pose.bones['Properties']
camera = scene.camera
camera_state = camera.matrix_world.copy(), camera.data.type, camera.data.ortho_scale
frame = scene.frame_current
arm_state = {name: properties[name] for name in ('ik_left_arm', 'ik_right_arm')}
controls = {side: rig.pose.bones['FK-Hand.' + side] for side in ('L', 'R')}
control_state = {side: (bone.rotation_mode, bone.matrix_basis.copy())
                 for side, bone in controls.items()}


def evaluated_positions(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get('co', positions)
        return positions.reshape(-1, 3).copy()
    finally:
        evaluated.to_mesh_clear()


report = {}
try:
    scene.frame_set(1)
    for name in arm_state:
        properties[name] = 0.0
    rig.update_tag()
    bpy.context.view_layer.update()
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
    for side, sign in (('L', 1), ('R', -1)):
        hand = scene.objects['V353_ANATOMICAL_HAND.' + side]
        control = controls[side]
        before = evaluated_positions(hand)
        before_tail = rig.pose.bones['DEF-Hand.' + side].tail.copy()
        control.rotation_mode = 'XYZ'
        control.rotation_euler = (.35, .20 * sign, .12 * sign)
        rig.update_tag()
        bpy.context.view_layer.update()
        after = evaluated_positions(hand)
        displacement = np.linalg.norm(after - before, axis=1)
        tail_motion = (rig.pose.bones['DEF-Hand.' + side].tail - before_tail).length
        if not np.isfinite(after).all() or not .005 < float(displacement.max()) < .15:
            raise RuntimeError(f'{side}: hand did not make a bounded, measurable wrist bend')
        if tail_motion < .005:
            raise RuntimeError(f'{side}: DEF-Hand was not driven by the wrist control')
        camera.location = (sign * 1.2, -.18, .875)
        target = Vector((sign * .30, .01, .85))
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'v353_cuff_{side}_wrist_bend.png')
        bpy.ops.render.render(write_still=True)
        report[side] = {
            'control': control.name, 'arm_mode': 'FK',
            'rotation_radians': list(control.rotation_euler),
            'maximum_vertex_displacement_mm': float(displacement.max()) * 1000,
            'mean_vertex_displacement_mm': float(displacement.mean()) * 1000,
            'def_hand_tail_displacement_mm': tail_motion * 1000,
            'image': scene.render.filepath,
        }
        control.rotation_mode, control.matrix_basis = control_state[side]
        rig.update_tag()
        bpy.context.view_layer.update()
finally:
    for side, control in controls.items():
        control.rotation_mode, control.matrix_basis = control_state[side]
    for name, value in arm_state.items():
        properties[name] = value
    camera.matrix_world, camera.data.type, camera.data.ortho_scale = camera_state
    scene.frame_set(frame)
    rig.update_tag()
    bpy.context.view_layer.update()

path = out / 'preview_report.json'
previous = json.loads(path.read_text()) if path.exists() else {}
previous.pop('wrist_test_rotation_radians', None)
previous['wrist_deformation_test'] = report
previous['wrist_test_note'] = 'Replaces the earlier inactive FK test; actual evaluated mesh motion measured.'
path.write_text(json.dumps(previous, indent=2))
print(json.dumps(report))
