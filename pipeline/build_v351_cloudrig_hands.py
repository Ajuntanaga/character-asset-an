"""Replace fused Tripo hands with CC0 topology and fit native CloudRig fingers.

Run inside the existing Blender MCP session. V350 and source assets are retained.
The cuff classification records UV texture samples from the unchanged V350 mesh.
"""
import bpy
import bmesh
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v351_cloudrig_fingers'
OUT.mkdir(exist_ok=True)
scene = bpy.data.scenes.get('V351_CLOUDRIG_HANDS')
if scene is None:
    with bpy.data.libraries.load(str(ROOT / 'production_v350_tripo_cloudrig_body/Character_An_CloudRig_body_v350.blend'), link=False) as (src, dst):
        dst.scenes = ['V350_TRIPO_CLOUDRIG_BODY']
    scene = dst.scenes[0]
    scene.name = 'V351_CLOUDRIG_HANDS'
    for obj in scene.objects:
        if obj.name.startswith('V350_'):
            obj.name = obj.name.replace('V350_', 'V351_', 1).removesuffix('.001')
bpy.context.window.scene = scene
if scene.get('v351_hands_built'):
    raise RuntimeError('V351 already built; preserve it and use a new revision')
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
scene.frame_set(1)
body = scene.objects['V351_TRIPO_CHARACTER_BODY_BOUND']
meta = scene.objects['V351_CLOUDRIG_METARIG']
rig = scene.objects['V351_CLOUDRIG_CONTROLS']
if rig.animation_data:
    rig.animation_data.action = None
assert len(body.data.vertices) == 253390, 'Cuff map requires unchanged V350 source'

source = bpy.data.objects.get('V351_REALISTIC_HAND_SOURCE')
if source is None:
    library = ROOT / 'third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
    with bpy.data.libraries.load(str(library), link=False) as (src, dst):
        dst.objects = ['Hand  - Realistic']
    source = dst.objects[0]
assert len(source.data.vertices) == 831

# The first twenty quads form five integrated nail plates in this CC0 mesh.
skin = bpy.data.materials.new('V351_Warm_Brown_Hand_Skin')
skin.diffuse_color = (.36, .16, .087, 1)
skin.use_nodes = True
nodes, links = skin.node_tree.nodes, skin.node_tree.links
shader = nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = skin.diffuse_color
shader.inputs['Roughness'].default_value = .46
shader.inputs['Subsurface Weight'].default_value = .14
shader.inputs['Subsurface Radius'].default_value = (1, .38, .22)
shader.inputs['Subsurface Scale'].default_value = .0015
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 800
noise.inputs['Detail'].default_value = 2
tex = nodes.new('ShaderNodeTexCoord')
links.new(tex.outputs['Object'], noise.inputs['Vector'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .12
bump.inputs['Distance'].default_value = .00013
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], shader.inputs['Normal'])
nail = bpy.data.materials.new('V351_Natural_Keratin_Nails')
nail.diffuse_color = (.43, .24, .18, 1)
nail.use_nodes = True
nail_shader = nail.node_tree.nodes.get('Principled BSDF')
nail_shader.inputs['Base Color'].default_value = nail.diffuse_color
nail_shader.inputs['Roughness'].default_value = .30
nail_shader.inputs['Coat Weight'].default_value = .14
nail_shader.inputs['Subsurface Weight'].default_value = .10
nail_shader.inputs['Subsurface Scale'].default_value = .0005

source_cap = Vector((.00458, -.01076, .07447))
digit_points = {
    'Index': [(.032, -.001, -.103), (.045, -.001, -.143), (.051, .008, -.170), (.054, .013, -.189)],
    'Middle': [(.012, -.001, -.110), (.014, -.001, -.149), (.017, .008, -.181), (.018, .015, -.204)],
    'Ring': [(-.013, 0, -.105), (-.014, .001, -.145), (-.013, .015, -.170), (-.012, .022, -.194)],
    'Pinky': [(-.034, .009, -.098), (-.043, .012, -.128), (-.049, .017, -.146), (-.052, .022, -.165)],
    'Thumb': [(.022, .012, -.026), (.053, .020, -.060), (.073, .023, -.090), (.089, .026, -.111)],
}
hands, transforms, palms = {}, {}, {}
for side, sign in (('L', 1), ('R', -1)):
    z_axis = Vector((0, .16, .987)).normalized()
    x_axis = Vector((0, -z_axis.z, z_axis.y))
    palm_axis = Vector((-sign, 0, 0))
    basis = Matrix((x_axis * .76, palm_axis * .80, z_axis * .70)).transposed()
    transform = basis.to_4x4()
    transform.translation = Vector((sign * .302, .020, .920)) - basis @ source_cap
    transforms[side], palms[side] = transform, palm_axis
    hand = source.copy()
    hand.data = source.data.copy()
    hand.name = 'V351_ANATOMICAL_HAND.' + side
    scene.collection.objects.link(hand)
    hand.hide_render = False
    hand.hide_viewport = False
    hand.hide_set(False)
    hand.matrix_world = transform
    hand.data.materials.clear()
    hand.data.materials.append(skin)
    hand.data.materials.append(nail)
    for polygon in hand.data.polygons:
        polygon.material_index = 1 if polygon.index < 20 else 0
        polygon.use_smooth = True
    hand['source'] = 'Blender Studio Human Base Meshes v1.4.1 / Hand  - Realistic / CC0'
    hand['topology'] = '831 base vertices; 820 polygons; five separate digits and integrated nails'
    hands[side] = hand

# Keep the uneven, textured denim edge; remove only the old skin underneath it.
cuff = np.load(OUT / 'cuff_faces_classified.npz')
remove = cuff['face'][(cuff['co'][:, 2] < .85) |
                      ((cuff['co'][:, 2] < .908) & cuff['skin'])]
bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[int(i)] for i in remove], context='FACES')
bm.to_mesh(body.data)
bm.free()
body.data.update()

meta.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
bpy.ops.object.mode_set(mode='EDIT')
bones = meta.data.edit_bones
fit = {}
for side in ('L', 'R'):
    transform, palm = transforms[side], palms[side]
    for digit, points in digit_points.items():
        points = [Vector(p) for p in points]
        if digit != 'Thumb':
            carpal = bones[f'Finger_{digit}_Carpal.{side}']
            root = Vector((.003 + .25 * (points[0].x - .003), .001, -.012))
            carpal.head, carpal.tail = transform @ root, transform @ points[0]
            carpal.align_roll(palm)
        for i in range(3):
            bone = bones[f'Finger_{digit}{i + 1}.{side}']
            bone.head, bone.tail = transform @ points[i], transform @ points[i + 1]
            bone.align_roll(palm)
            fit[bone.name] = {'head': list(bone.head), 'tail': list(bone.tail)}
    hand_bone = bones['Hand.' + side]
    hand_bone.tail = transform @ Vector((.003, .001, -.012))
    hand_bone.align_roll(palm)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.pose.cloudrig_generate(focus_generated=True, preserve_state=False)
rig = meta.cloudrig.generator.target_rig
if rig is None or rig.name.startswith('FAILED-'):
    raise RuntimeError('CloudRig generation failed')
rig.name = 'V351_CLOUDRIG_CONTROLS'
# Keep generated IK/FK and deformation drivers; detach only the old action.
if rig.animation_data:
    rig.animation_data.action = None
body_matrix = body.matrix_world.copy()
body.parent = rig
body.matrix_world = body_matrix
for modifier in body.modifiers:
    if modifier.type == 'ARMATURE':
        modifier.object = rig
meta.hide_set(True)
meta.hide_render = True

original_deform = {b.name: b.use_deform for b in rig.data.bones}
binding = {}
try:
    for side, hand in hands.items():
        for bone in rig.data.bones:
            bone.use_deform = bone.name == 'DEF-Hand.' + side or (
                bone.name.startswith('DEF-Finger_') and bone.name.endswith('.' + side))
        bpy.ops.object.select_all(action='DESELECT')
        hand.select_set(True)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        armature = next(m for m in hand.modifiers if m.type == 'ARMATURE')
        armature.name = 'CloudRig individual finger deformation'
        armature.use_deform_preserve_volume = True
        hand.modifiers.move(list(hand.modifiers).index(armature), 0)
        multi = next(m for m in hand.modifiers if m.type == 'MULTIRES')
        bpy.context.view_layer.objects.active = hand
        while multi.total_levels < 3:
            bpy.ops.object.multires_subdivide(modifier=multi.name, mode='CATMULL_CLARK')
        multi.levels, multi.render_levels = 2, 3
        unweighted = sum(not any(g.weight > .00001 for g in v.groups) for v in hand.data.vertices)
        if unweighted:
            raise RuntimeError(f'{side}: {unweighted} unweighted hand vertices')
        binding[side] = {'vertices': len(hand.data.vertices), 'unweighted': unweighted,
                         'deform_bones': [b.name for b in rig.data.bones if b.use_deform]}
finally:
    for bone in rig.data.bones:
        bone.use_deform = original_deform[bone.name]

scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 1400
scene.view_settings.view_transform = 'AgX'
scene['v351_hands_built'] = True
scene['quality_status'] = 'Clean individually skinned hands; reference likeness, face, groom and guitar contact unfinished'
rig['face_and_finger_controls'] = 'Finger FK controls fitted and skinned; face remains unskinned'
scene.frame_set(1)
bpy.context.view_layer.update()
bpy.data.libraries.write(str(OUT / 'Character_An_CloudRig_hands_v351.blend'), {scene}, fake_user=True, compress=True)

# A reversible animation through actual animator-facing FK controls.
rest_tips = {s: {d: list(rig.pose.bones[f'DEF-Finger_{d}3.{s}'].tail)
                 for d in digit_points} for s in ('L', 'R')}
for side in ('L', 'R'):
    for digit in digit_points:
        for i in range(1, 4):
            control = rig.pose.bones[f'FK-Finger_{digit}{i}.{side}']
            control.rotation_mode = 'XYZ'
            control.rotation_euler = (0, 0, 0)
            control.keyframe_insert('rotation_euler', frame=1, group=control.name)
            control.keyframe_insert('rotation_euler', frame=48, group=control.name)
            degrees = (25, 35, 20) if digit == 'Thumb' else (55, 65, 35)
            control.rotation_euler.x = math.radians(degrees[i - 1])
            control.keyframe_insert('rotation_euler', frame=24, group=control.name)
scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 24
rig.animation_data.action.name = 'V351_Individual_Finger_Curl_Test_2s'
scene.frame_set(24)
bpy.context.view_layer.update()
posed_tips = {s: {d: list(rig.pose.bones[f'DEF-Finger_{d}3.{s}'].tail)
                  for d in digit_points} for s in ('L', 'R')}
warnings = [{'bone': log.base_bone_name, 'message': log.description_short,
             'fatal': log.is_fatal} for log in meta.cloudrig.generator.logs]
report = {'binding': binding, 'removed_old_skin_faces': len(remove),
          'body_vertices_after_cuff_trim': len(body.data.vertices),
          'rest_tips': rest_tips, 'posed_tips': posed_tips,
          'generation_warnings': warnings, 'visual_review': 'pending'}
(OUT / 'hand_binding.json').write_text(json.dumps(report, indent=2))
(OUT / 'metarig_finger_fit.json').write_text(json.dumps(fit, indent=2))
bpy.data.libraries.write(str(OUT / 'Character_An_CloudRig_hands_pose_v351.blend'), {scene}, fake_user=True, compress=True)
print(json.dumps(report))
