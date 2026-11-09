"""Fit a copy of the official Sintel CloudRig and bind a body-motion candidate.

The original dense asset and reusable template stay untouched. Face and finger
deformation deliberately remain unbound until those surfaces are rebuilt.
"""
import bpy
import json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v350_tripo_cloudrig_body'
OUT.mkdir(exist_ok=True)
if bpy.data.scenes.get('V350_TRIPO_CLOUDRIG_BODY'):
    raise RuntimeError('V350 exists; inspect it before rerunning')

source_scene = bpy.data.scenes['V349_TRIPO_RIG_CANDIDATE']
scene = bpy.data.scenes.new('V350_TRIPO_CLOUDRIG_BODY')
bpy.context.window.scene = scene
scene.world = source_scene.world
for original in source_scene.objects:
    obj = original.copy()
    obj.data = original.data.copy()
    scene.collection.objects.link(obj)
    if original.name == 'V349_TRIPO_CHARACTER_SOURCE':
        character = obj
        character.name = 'V350_TRIPO_CHARACTER_BODY_BOUND'
    elif obj.type == 'CAMERA':
        scene.camera = obj
        obj.name = 'V350_CAMERA'

template = bpy.data.objects['V348_CLOUDRIG_SINTEL_METARIG_TEMPLATE']
meta = template.copy()
meta.data = template.data.copy()
meta.name = 'V350_CLOUDRIG_METARIG'
meta.cloudrig.generator.target_rig = None
scene.collection.objects.link(meta)
meta.hide_set(False)
meta.hide_viewport = False
meta.matrix_world = Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT')
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
bpy.ops.object.mode_set(mode='EDIT')
bones = meta.data.edit_bones
original = {b.name: (b.head.copy(), b.tail.copy()) for b in bones}

# A coarse face fit retains the complete control topology, but no face weights
# are assigned. The generated texture currently contains the eyes and lips.
for b in bones:
    for attr in ('head', 'tail'):
        p = getattr(b, attr).copy()
        if p.z > 1.42:
            p = Vector((p.x * 1.15, p.y * 1.10 + .018,
                        1.535 + (p.z - 1.4276) * 1.10))
        else:
            p = Vector((p.x * 1.10, p.y + .07, p.z * 1.08))
        setattr(b, attr, p)

def set_bone(name, head, tail):
    bones[name].head = head
    bones[name].tail = tail

set_bone('root', (0, 0, 0), (0, .35, 0))
set_bone('Hips', (0, .065, .88), (0, .07, 1.02))
set_bone('Spine', (0, .07, 1.02), (0, .065, 1.19))
set_bone('Chest', (0, .065, 1.19), (0, .055, 1.43))
set_bone('Neck', (0, .055, 1.43), (0, .035, 1.535))
set_bone('Head', (0, .035, 1.535), (0, .015, 1.78))

for side, sign in (('L', 1), ('R', -1)):
    shoulder = Vector((sign * .19, .065, 1.41))
    elbow = Vector((sign * .267, .075, 1.17))
    wrist = Vector((sign * .302, .020, .92))
    palm = Vector((sign * .301, -.005, .866))
    set_bone('Shoulder.' + side, (sign * .035, .045, 1.415), shoulder)
    set_bone('UpperArm.' + side, shoulder, elbow)
    set_bone('Forearm.' + side, elbow, wrist)
    set_bone('Hand.' + side, wrist, palm)
    old_wrist = original['Hand.' + side][0]
    for b in bones:
        if b.name.startswith('Finger_') and b.name.endswith('.' + side):
            for attr, p in zip(('head', 'tail'), original[b.name]):
                delta = p - old_wrist
                distance = delta.x * sign
                # Thumb toward the body, palm inward, relaxed finger curve.
                point = wrist + Vector((sign * delta.y * .9,
                                        -delta.z * .85 - .27 * distance,
                                        -.65 * distance))
                setattr(b, attr, point)

    hip = Vector((sign * .105, .070, .94))
    knee = Vector((sign * .145, .035, .55))
    ankle = Vector((sign * .155, .080, .19))
    ball = Vector((sign * .174, -.035, .055))
    toe = Vector((sign * .190, -.120, .035))
    set_bone('Thigh.' + side, hip, knee)
    set_bone('Knee.' + side, knee, ankle)
    set_bone('Foot.' + side, ankle, ball)
    set_bone('Toes.' + side, ball, toe)
    set_bone('Hip.' + side, (sign * .105, .070, .87), hip)
    set_bone('HeelPivot.' + side, (sign * .12, .13, .015),
             (sign * .20, .13, .015))

    # CloudRig's hinge constraint expects the bend axis to be local X.
    for names in (('UpperArm.' + side, 'Forearm.' + side),
                  ('Thigh.' + side, 'Knee.' + side)):
        upper, lower = (bones[n] for n in names)
        normal = (upper.tail - upper.head).cross(lower.tail - lower.head).normalized()
        for b in (upper, lower):
            b.align_roll(normal.cross((b.tail - b.head).normalized()))

fit = {b.name: {'head': list(b.head), 'tail': list(b.tail)} for b in bones}
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.pose.cloudrig_generate(focus_generated=True, preserve_state=False)
rig = meta.cloudrig.generator.target_rig
if rig is None or rig.name.startswith('FAILED-'):
    raise RuntimeError('CloudRig generation failed')
rig.name = 'V350_CLOUDRIG_CONTROLS'
rig.show_in_front = True
meta.hide_set(True)
meta.hide_render = True

body_names = {'DEF-Hips', 'DEF-Spine', 'DEF-Chest', 'DEF-Neck', 'DEF-Head'}
body_prefixes = ('DEF-Shoulder.', 'DEF-UpperArm_', 'DEF-Forearm_', 'DEF-Hand.',
                 'DEF-Thigh_', 'DEF-Knee_', 'DEF-Foot.', 'DEF-Toes.', 'DEF-Hip.')
original_deform = {b.name: b.use_deform for b in rig.data.bones}
for b in rig.data.bones:
    b.use_deform = b.name in body_names or b.name.startswith(body_prefixes)
binding_bones = [b.name for b in rig.data.bones if b.use_deform]

# A watertight volume proxy makes heat weighting independent of UV splits,
# overlapping clothing seams and tiny generated surface fragments.
proxy = character.copy()
proxy.data = character.data.copy()
proxy.name = 'V350_BODY_WEIGHT_PROXY'
scene.collection.objects.link(proxy)
bpy.ops.object.select_all(action='DESELECT')
proxy.select_set(True)
bpy.context.view_layer.objects.active = proxy
remesh = proxy.modifiers.new('Weight volume at 12mm', 'REMESH')
remesh.mode = 'VOXEL'
remesh.voxel_size = .012
remesh.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier=remesh.name)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
unweighted = sum(not any(g.weight > .00001 for g in v.groups) for v in proxy.data.vertices)
if unweighted:
    raise RuntimeError(f'Heat weights left {unweighted} proxy vertices unweighted')

for group in proxy.vertex_groups:
    character.vertex_groups.new(name=group.name)
bpy.ops.object.select_all(action='DESELECT')
character.select_set(True)
bpy.context.view_layer.objects.active = character
transfer = character.modifiers.new('Transfer smooth body weights', 'DATA_TRANSFER')
transfer.object = proxy
transfer.use_vert_data = True
transfer.data_types_verts = {'VGROUP_WEIGHTS'}
transfer.vert_mapping = 'POLYINTERP_NEAREST'
transfer.layers_vgroup_select_src = 'ALL'
transfer.layers_vgroup_select_dst = 'NAME'
bpy.ops.object.modifier_apply(modifier=transfer.name)
unweighted = sum(not any(g.weight > .00001 for g in v.groups) for v in character.data.vertices)
if unweighted:
    raise RuntimeError(f'Transfer left {unweighted} character vertices unweighted')
armature = character.modifiers.new('CloudRig body skin', 'ARMATURE')
armature.object = rig
armature.use_deform_preserve_volume = True
character.parent = rig
proxy.hide_render = True
proxy.hide_set(True)
for b in rig.data.bones:
    b.use_deform = original_deform[b.name]

scene.camera.data.lens = 60
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 1400
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene['quality_status'] = 'Body skinned candidate; face/finger weights and deformation review pending'
character['rig_status'] = scene['quality_status']
rig['face_and_finger_controls'] = 'Generated and approximately fitted, not skinned'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.overlay.show_overlays = False
            area.spaces.active.region_3d.view_perspective = 'CAMERA'

report = {'rig': rig.name, 'bones': len(rig.data.bones),
          'body_binding_bones': binding_bones,
          'proxy_vertices': len(proxy.data.vertices),
          'character_vertices': len(character.data.vertices),
          'unweighted_vertices': unweighted,
          'face_and_fingers_skinned': False,
          'deformation_review': 'pending'}
(OUT / 'body_binding.json').write_text(json.dumps(report, indent=2))
(OUT / 'metarig_fit.json').write_text(json.dumps(fit, indent=2))
bpy.data.libraries.write(str(OUT / 'Character_An_CloudRig_body_v350.blend'), {scene},
                         fake_user=True, compress=True)
print(json.dumps(report))
