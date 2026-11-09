"""Correct CloudRig limb planes, then save a body-control motion test."""
import bpy
import json
import math
from pathlib import Path

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v350_tripo_cloudrig_body'
scene = bpy.data.scenes['V350_TRIPO_CLOUDRIG_BODY']
bpy.context.window.scene = scene
meta = bpy.data.objects['V350_CLOUDRIG_METARIG']
character = bpy.data.objects['V350_TRIPO_CHARACTER_BODY_BOUND']
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
meta.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
bpy.ops.object.mode_set(mode='POSE')
fixes = [json.loads(log.op_kwargs) for log in meta.cloudrig.generator.logs
         if log.operator == 'armature.flatten_ik_chain']
for kwargs in fixes:
    kwargs['remove_active_log'] = False
    kwargs['pole_axis'] = '-Z'
    if kwargs.get('start_bone', '').startswith('Thigh'):
        kwargs['limit_count'] = 4
    bpy.ops.armature.flatten_ik_chain(**kwargs)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.pose.cloudrig_generate(focus_generated=True, preserve_state=False)
rig = meta.cloudrig.generator.target_rig
rig.name = 'V350_CLOUDRIG_CONTROLS'
character.parent = rig
for modifier in character.modifiers:
    if modifier.type == 'ARMATURE':
        modifier.object = rig
meta.hide_set(True)
logs = [{'bone': log.base_bone_name, 'message': log.description_short,
         'description': log.description, 'fatal': log.is_fatal}
        for log in meta.cloudrig.generator.logs]
body_errors = [log for log in logs if log['bone'].startswith(('UpperArm', 'Thigh'))
               and ('IK' in log['message'] or log['fatal'])]
if body_errors:
    raise RuntimeError(f'Body IK still invalid: {body_errors}')
(OUT / 'generation_warnings.json').write_text(json.dumps(logs, indent=2))
scene.frame_set(1)
scene['quality_status'] = 'Body skin candidate; face and fingers not skinned'
bpy.data.libraries.write(str(OUT / 'Character_An_CloudRig_body_v350.blend'),
                         {scene}, fake_user=True, compress=True)

# Work only through animator-facing FK controls. The production rest copy
# above remains available independently from this two-second test action.
properties = rig.pose.bones['Properties']
properties['ik_left_arm'] = 0.0
properties['ik_right_arm'] = 0.0
rig.update_tag()
bpy.context.view_layer.update()
controls = [rig.pose.bones['FK-Forearm.' + s] for s in ('L', 'R')]
controls += [rig.pose.bones['FK-Head']]
for bone in controls:
    bone.rotation_euler = (0, 0, 0)
    bone.keyframe_insert('rotation_euler', frame=1, group=bone.name)
    bone.keyframe_insert('rotation_euler', frame=48, group=bone.name)
rest_hands = {s: list(rig.pose.bones['DEF-Hand.' + s].head) for s in ('L', 'R')}
scene.frame_set(24)
for side, angle in (('L', math.radians(52)), ('R', math.radians(32))):
    bone = rig.pose.bones['FK-Forearm.' + side]
    bone.rotation_euler.x = angle
    bpy.context.view_layer.update()
    if rig.pose.bones['DEF-Hand.' + side].head.y > rest_hands[side][1]:
        bone.rotation_euler.x = -angle
        bpy.context.view_layer.update()
    bone.keyframe_insert('rotation_euler', frame=24, group=bone.name)
head = rig.pose.bones['FK-Head']
head.rotation_euler.y = math.radians(8)
head.keyframe_insert('rotation_euler', frame=24, group=head.name)
scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 24
rig.animation_data.action.name = 'V350_Body_Control_Test_2s'
bpy.context.view_layer.update()
pose_hands = {s: list(rig.pose.bones['DEF-Hand.' + s].head) for s in ('L', 'R')}
for side in ('L', 'R'):
    if pose_hands[side][1] > rest_hands[side][1] - .06:
        raise RuntimeError('FK forearm did not move hand forward: ' + side)
scene['quality_status'] = 'Body control motion test; pending visual review; face and fingers unskinned'
bpy.data.libraries.write(str(OUT / 'Character_An_CloudRig_body_pose_v350.blend'),
                         {scene}, fake_user=True, compress=True)
report = {'rest_hands': rest_hands, 'posed_hands': pose_hands,
          'controls': [b.name for b in controls], 'action': rig.animation_data.action.name,
          'frames': [1, 24, 48], 'remaining_generation_warnings': len(logs),
          'face_and_fingers_skinned': False, 'visual_review': 'pending'}
(OUT / 'pose_test.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
