"""Repair V351 finger bend planes inside the remote Blender worker."""
import importlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    source = Path(os.environ['BCA_SOURCE'])
    out = Path(os.environ['BCA_OUTPUT'])
    out.mkdir(parents=True, exist_ok=True)
    # Register the same vendored CloudRig package without requiring desktop UI.
    sys.path.insert(0, '/opt/addons')
    if 'cloudrig' not in bpy.context.preferences.addons:
        bpy.context.preferences.addons.new().module = 'cloudrig'
    cloudrig = importlib.import_module('cloudrig')
    cloudrig.register()
    bpy.context.preferences.filepaths.use_scripts_auto_execute = True
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.data.scenes['V351_CLOUDRIG_HANDS']
    bpy.context.window.scene = scene
    for unused_scene in list(bpy.data.scenes):
        if unused_scene != scene:
            bpy.data.scenes.remove(unused_scene)
    scene.frame_set(1)
    meta = scene.objects['V351_CLOUDRIG_METARIG']
    old_rig = scene.objects['V351_CLOUDRIG_CONTROLS']
    if old_rig.animation_data:
        old_rig.animation_data.action = None
    deform_objects = [scene.objects['V351_TRIPO_CHARACTER_BODY_BOUND']]
    deform_objects += [scene.objects['V351_ANATOMICAL_HAND.' + s] for s in ('L', 'R')]
    matrices = {obj.name: obj.matrix_world.copy() for obj in deform_objects}
    before = {'mirror_x': meta.data.use_mirror_x}
    meta.data.use_mirror_x = False
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    meta.hide_set(False)
    meta.hide_viewport = False
    bpy.ops.object.select_all(action='DESELECT')
    meta.select_set(True)
    bpy.context.view_layer.objects.active = meta
    bpy.ops.object.mode_set(mode='POSE')
    for side in ('L', 'R'):
        bpy.ops.armature.flatten_ik_chain(start_bone='UpperArm.' + side,
            limit_count=3, pole_axis='-Z', remove_active_log=False)
        for digit in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb'):
            bpy.ops.armature.flatten_ik_chain(start_bone=f'Finger_{digit}1.{side}',
                limit_count=3, pole_axis='-Z', remove_active_log=False)
    bpy.ops.object.mode_set(mode='EDIT')
    axes = {}
    for side, sign in (('L', 1), ('R', -1)):
        palm = Vector((-sign, 0, 0))
        for digit in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb'):
            for index in range(1, 4):
                bone = meta.data.edit_bones[f'Finger_{digit}{index}.{side}']
                # A half-turn keeps the IK plane valid and makes +X curl palmar.
                if bone.z_axis.dot(palm) < 0:
                    bone.roll += math.pi
                axes[bone.name] = {'z_dot_palm': bone.z_axis.dot(palm),
                                   'head': list(bone.head), 'tail': list(bone.tail)}
                if bone.z_axis.dot(palm) < .5:
                    raise RuntimeError('Finger bend axis does not face palm: ' + bone.name)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.pose.cloudrig_generate(focus_generated=False, preserve_state=False)
    rig = meta.cloudrig.generator.target_rig
    if rig is None or rig.name.startswith('FAILED-'):
        raise RuntimeError('CloudRig generation failed')
    # animation_data_clear() also removes the newly generated CloudRig drivers.
    if rig.animation_data:
        rig.animation_data.action = None
    for obj in deform_objects:
        obj.parent = rig
        obj.matrix_world = matrices[obj.name]
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.object = rig
    warnings = [{'bone': log.base_bone_name, 'message': log.description_short,
                 'fatal': log.is_fatal} for log in meta.cloudrig.generator.logs]
    errors = [w for w in warnings if w['fatal'] or
              (w['bone'].startswith(('UpperArm', 'Finger_')) and 'IK' in w['message'])]
    if errors:
        raise RuntimeError('Unrepaired rig errors: ' + json.dumps(errors))
    meta.hide_set(True)
    meta.hide_render = True
    scene.name = 'V352_CLOUDRIG_HANDS'
    for obj in scene.objects:
        if obj.name.startswith('V351_'):
            obj.name = obj.name.replace('V351_', 'V352_', 1)
    rig.name = 'V352_CLOUDRIG_CONTROLS'
    meta.name = 'V352_CLOUDRIG_METARIG'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    scene['quality_status'] = 'Finger-axis repair candidate; face, hair, cuffs and guitar contact unfinished'
    bpy.context.view_layer.update()
    rest = {s: {d: list(rig.pose.bones[f'DEF-Finger_{d}3.{s}'].tail)
                for d in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')} for s in ('L', 'R')}
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Character_An_CloudRig_hands_v352.blend'),
                              compress=True)
    for side in ('L', 'R'):
        for digit in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb'):
            for index in range(1, 4):
                control = rig.pose.bones[f'FK-Finger_{digit}{index}.{side}']
                control.rotation_mode = 'XYZ'
                control.rotation_euler = (0, 0, 0)
                control.keyframe_insert('rotation_euler', frame=1, group=control.name)
                control.keyframe_insert('rotation_euler', frame=48, group=control.name)
                angles = (25, 35, 20) if digit == 'Thumb' else (55, 65, 35)
                control.rotation_euler.x = math.radians(angles[index - 1])
                control.keyframe_insert('rotation_euler', frame=24, group=control.name)
    scene.frame_start, scene.frame_end = 1, 48
    scene.render.fps = 24
    rig.animation_data.action.name = 'V352_Individual_Finger_Curl_Test_2s'
    scene.frame_set(24)
    bpy.context.view_layer.update()
    posed, inward, inward_fraction = {}, {}, {}
    for side, sign in (('L', 1), ('R', -1)):
        posed[side], inward[side], inward_fraction[side] = {}, {}, {}
        for digit in rest[side]:
            tip = rig.pose.bones[f'DEF-Finger_{digit}3.{side}'].tail.copy()
            posed[side][digit] = list(tip)
            inward[side][digit] = (tip - Vector(rest[side][digit])).dot(Vector((-sign, 0, 0)))
            length = sum(rig.data.bones[f'DEF-Finger_{digit}{index}.{side}'].length
                         for index in range(1, 4))
            inward_fraction[side][digit] = inward[side][digit] / length
            # A tightly curled fingertip can finish close to the palm plane.
            # Check inward motion relative to finger size, then inspect the render.
            if inward_fraction[side][digit] < .05:
                raise RuntimeError(f'{side} {digit} did not curl toward palm: {inward[side][digit]}')
    report = {'before': before, 'axes': axes, 'rest_tips': rest, 'posed_tips': posed,
              'inward_tip_displacement_m': inward,
              'inward_tip_displacement_fraction': inward_fraction, 'warnings': warnings,
              'visual_review': 'pending remote renders', 'compute_location': 'Modal'}
    (out / 'finger_axis_report.json').write_text(json.dumps(report, indent=2))
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Character_An_CloudRig_hands_pose_v352.blend'),
                              compress=True)
    print('V352_REMOTE_RIG_SAVED', json.dumps(inward), flush=True)


if __name__ == '__main__':
    main()
