"""Give the unfolding eyelids a two-dimensional skin patch and refine skin."""
from collections import defaultdict, deque
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v372_face_surface'
OUT.mkdir(exist_ok=True)
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
mesh = body.data
keys = mesh.shape_keys.key_blocks
source = bpy.data.meshes['V362_BODY_BEFORE_EYE_SOCKETS']
coords = [v.co.copy() for v in source.vertices]
bvh = BVHTree.FromPolygons(coords, [list(f.vertices) for f in source.polygons])
landmarks = json.loads((ROOT/'production_v362_face_anatomy/actual_face_landmarks.json').read_text())['landmarks']


def sample_uv(x, z):
    p, _, index, _ = bvh.ray_cast(Vector((x, -.7, z)), Vector((0, 1, 0)))
    if p is None:
        raise ValueError((x, z))
    f = source.polygons[index]
    vi, li = list(f.vertices)[:3], list(f.loop_indices)[:3]
    uv = [Vector((*source.uv_layers.active.data[j].uv, 0)) for j in li]
    return barycentric_transform(p, *[coords[j] for j in vi], *uv).xy


def interp(points, x):
    for a, b in zip(points, points[1:]):
        if a.x <= x <= b.x:
            return a.lerp(b, (x-a.x)/(b.x-a.x))
    return (points[0] if x < points[0].x else points[-1]).copy()


def smooth(a):
    a = min(1., max(0., a))
    return a*a*(3-2*a)


lid_index = list(mesh.materials).index(bpy.data.materials['V365_LID_SKIN'])
lid_faces = [f for f in mesh.polygons if f.material_index == lid_index]
uv = mesh.uv_layers['V365_CleanSkin']
updated = set()
for side in ('L', 'R'):
    upper = [Vector(v['world']) for v in landmarks[side]['upper']]
    lower = [Vector(v['world']) for v in landmarks[side]['lower']]
    midx = (upper[0].x+upper[-1].x)/2
    for f in lid_faces:
        if (keys['Basis'].data[f.vertices[0]].co.x > 0) != (side == 'L'):
            continue
        for li in f.loop_indices:
            vi = mesh.loops[li].vertex_index
            p = keys['Basis'].data[vi].co
            closed = keys['Blink.'+side].data[vi].co
            seam = .23*interp(upper, p.x).z + .77*interp(lower, p.x).z
            # A forehead patch gives both UV dimensions physical extent even
            # when the lid is closed. The original blend returns to the scan
            # UVs at the welded outer boundary.
            sx = .85*p.x
            sz = 1.681 + .72*abs(closed.z-seam)
            uv.data[li].uv = sample_uv(sx, sz)
            updated.add(vi)

rest = mesh.attributes.get('V372_RestPosition') or mesh.attributes.new('V372_RestPosition', 'FLOAT_VECTOR', 'POINT')
weight = mesh.attributes.get('V372_HeadSkin') or mesh.attributes.new('V372_HeadSkin', 'FLOAT', 'POINT')
for v in mesh.vertices:
    p = keys['Basis'].data[v.index].co
    rest.data[v.index].vector = p
    weight.data[v.index].value = smooth((p.z-1.465)/.040)

face = bpy.data.materials.get('V372_FACE_SKIN')
if face is None:
    face = mesh.materials[0].copy()
    face.name = 'V372_FACE_SKIN'
if face.name not in mesh.materials:
    mesh.materials.append(face)
face_index = list(mesh.materials).index(face)
for f in mesh.polygons:
    if f.material_index in (0, face_index) and any(keys['Basis'].data[i].co.z > 1.465 for i in f.vertices):
        f.material_index = face_index

for mat in (face, bpy.data.materials['V365_LID_SKIN']):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes['Principled BSDF']
    existing = nodes.get('V372_Complexion')
    if existing is None:
        original = shader.inputs['Base Color'].links[0].from_socket
        correction = nodes.new('ShaderNodeMixRGB')
        correction.name = 'V372_Complexion'
        correction.label = 'Warm brown complexion from the approved sheet'
        correction.blend_type = 'MULTIPLY'
        correction.inputs[2].default_value = (.66, .57, .48, 1.)
        attribute = nodes.new('ShaderNodeAttribute')
        attribute.attribute_name = 'V372_HeadSkin'
        links.new(attribute.outputs['Fac'], correction.inputs[0])
        links.new(original, correction.inputs[1])
        links.new(correction.outputs[0], shader.inputs['Base Color'])
        position = nodes.new('ShaderNodeAttribute')
        position.attribute_name = 'V372_RestPosition'
        noise = nodes.new('ShaderNodeTexNoise')
        noise.name = 'V372_SkinMicrorelief'
        noise.inputs['Scale'].default_value = 3600.
        noise.inputs['Detail'].default_value = 2.
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .18
        bump.inputs['Distance'].default_value = .000055
        links.new(position.outputs['Vector'], noise.inputs['Vector'])
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    shader.inputs['Roughness'].default_value = .48
    shader.inputs['Specular IOR Level'].default_value = .30
    shader.inputs['Subsurface Weight'].default_value = .065
    shader.inputs['Subsurface Scale'].default_value = .0013
    shader.inputs['Subsurface Radius'].default_value = (1., .48, .25)

# The scan's low inner brows read as a frown. An independently controlled
# corrective lifts their inner third without moving the closing lid edges.
relax = keys.get('BrowInnerUp') or body.shape_key_add(name='BrowInnerUp')
for v, b in zip(relax.data, keys['Basis'].data):
    p = b.co.copy()
    front = smooth((-.035-p.y)/.025)
    upper = smooth((p.z-1.656)/.007)
    amount = .006*math.exp(-((abs(p.x)-.018)/.021)**2-((p.z-1.666)/.016)**2)*front*upper
    p.z += amount
    v.co = p
head['BrowInnerUp'] = .50
head.id_properties_ui('BrowInnerUp').update(min=0., max=1., description='Lift the inner brows')
key_animation = mesh.shape_keys.animation_data
key_path = relax.path_from_id('value')
existing_driver = (next((curve for curve in key_animation.drivers
                         if curve.data_path == key_path), None)
                   if key_animation else None)
if existing_driver is None:
    driver = relax.driver_add('value').driver
    driver.type = 'SCRIPTED'
    variable = driver.variables.new(); variable.name = 'v'; variable.type = 'SINGLE_PROP'
    variable.targets[0].id = rig
    variable.targets[0].data_path = 'pose.bones["Head"]["BrowInnerUp"]'
    driver.expression = 'v'
mesh.update(); rig.update_tag(); bpy.context.view_layer.update()
assert len(rig.animation_data.drivers) == 1957

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'; scene.cycles.samples = 32
scene.render.threads_mode = 'FIXED'; scene.render.threads = 1
scene.render.resolution_x = scene.render.resolution_y = 640
scene.camera.data.ortho_scale = .37
scene.camera.location = (0, -1.4, 1.66)
scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
for name, value in [('neutral', 0.), ('blink', 1.)]:
    head['Blink.L'] = head['Blink.R'] = value
    rig.update_tag(); bpy.context.view_layer.update()
    scene.render.filepath = str(OUT/f'v372_face_{name}.png')
    bpy.ops.render.render(write_still=True)
head['Blink.L'] = head['Blink.R'] = 0.
rig.update_tag(); bpy.context.view_layer.update()
report = {'lid_vertices_remapped': len(updated), 'skin_material': face.name,
          'shape_keys': list(keys.keys()), 'rig_drivers': len(rig.animation_data.drivers),
          'brow_neutral_control': head['BrowInnerUp']}
(OUT/'face_surface_report.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_face_surface_v372.blend'), compress=True)
print(json.dumps(report))
