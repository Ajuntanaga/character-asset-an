"""Regenerate CloudRig drivers without discarding the existing finger action."""
import bpy
import json
from pathlib import Path

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v354_rig_driver_repair'
out.mkdir(exist_ok=True)
scene = bpy.data.scenes['V353_CLOUDRIG_CUFFS']
bpy.context.window.scene = scene
scene.frame_set(1)
rig = scene.objects['V353_CLOUDRIG_CONTROLS']
meta = scene.objects['V353_CLOUDRIG_METARIG']
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
source_file = bpy.data.filepath
old_driver_count = len(rig.animation_data.drivers) if rig.animation_data else 0
action = rig.animation_data.action if rig.animation_data else None
action_slot = rig.animation_data.action_slot if action else None
if action:
    action.use_fake_user = True
bound = [obj for obj in scene.objects if any(
    modifier.type == 'ARMATURE' and modifier.object == rig for modifier in obj.modifiers)]
matrices = {obj.name: obj.matrix_world.copy() for obj in bound}
rest_heads = {bone.name: bone.head_local.copy() for bone in rig.data.bones if bone.use_deform}
meta.hide_set(False)
meta.hide_viewport = False
bpy.ops.object.select_all(action='DESELECT')
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
bpy.ops.pose.cloudrig_generate(focus_generated=False, preserve_state=True)
rig = meta.cloudrig.generator.target_rig
if rig is None or rig.name.startswith('FAILED-'):
    raise RuntimeError('CloudRig regeneration failed; V353 remains saved separately')
if not rig.animation_data or not rig.animation_data.drivers:
    raise RuntimeError('Regeneration produced no control drivers')
if action:
    rig.animation_data.action = action
    rig.animation_data.action_slot = action_slot
for obj in bound:
    obj.parent = rig
    obj.matrix_world = matrices[obj.name]
    for modifier in obj.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
meta.hide_set(True)
meta.hide_render = True
rig.hide_set(False)
scene.frame_set(1)
rig.update_tag()
bpy.context.view_layer.update()
rest_change = max((rig.data.bones[name].head_local - co).length for name, co in rest_heads.items())
if rest_change > .00001:
    raise RuntimeError(f'Regeneration unexpectedly changed the deformation rest pose: {rest_change}')
invalid = [driver.data_path for driver in rig.animation_data.drivers if not driver.driver.is_valid]
if invalid:
    raise RuntimeError('Invalid regenerated drivers: ' + json.dumps(invalid))
warnings = [{'bone': log.base_bone_name, 'message': log.description_short,
             'fatal': log.is_fatal} for log in meta.cloudrig.generator.logs]
if any(item['fatal'] for item in warnings):
    raise RuntimeError('Fatal CloudRig generation warning')
scene.name = 'V354_CLOUDRIG_DRIVERS'
for obj in scene.objects:
    if obj.name.startswith('V353_'):
        obj.name = obj.name.replace('V353_', 'V354_', 1)
rig.name = 'V354_CLOUDRIG_CONTROLS'
meta.name = 'V354_CLOUDRIG_METARIG'
scene['quality_status'] = 'Control drivers restored; wrist and finger deformation review pending'
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
report = {'source': source_file, 'previous_driver_count': old_driver_count,
          'restored_driver_count': len(rig.animation_data.drivers),
          'maximum_deform_rest_head_change_m': rest_change,
          'preserved_action': action.name if action else None,
          'bound_objects': [obj.name for obj in bound], 'warnings': warnings}
(out / 'rig_driver_repair.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Character_An_CloudRig_drivers_v354.blend'), compress=True)
print(json.dumps(report))
