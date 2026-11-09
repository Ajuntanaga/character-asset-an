"""Open the compact spiral guides into overlapping half-turn locks.

Run after V374 in the existing GUI. Preserve scalp roots, strand density,
material, face work, and CloudRig so the geometry comparison is useful.
"""
from collections import defaultdict
from pathlib import Path
import bisect
import json
import math
import random
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v375_overlapping_curls'
OUT.mkdir(exist_ok=True)
started = time.monotonic()
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957

data = json.loads((ROOT/'production_v371_curl_groom/scalp_surface.json').read_text())
mask = set(json.loads((ROOT/'production_v371_curl_groom/hair_mask.json').read_text())['faces'])
positions = {int(k): Vector(v) for k, v in data['vertices'].items()}
faces = [f for f in data['faces'] if f['id'] in mask]
index = {old: i for i, old in enumerate(positions)}
bvh = BVHTree.FromPolygons(list(positions.values()), [[index[v] for v in f['v']] for f in data['faces']], all_triangles=False)
areas = []
total = 0.
for face in faces:
    a, b, c = (positions[v] for v in face['v'])
    total += (b-a).cross(c-a).length/2
    areas.append(total)

# A blue-noise root layout leaves each curl enough space to read as a clump.
# Root spacing is in metres and therefore independent of texture resolution.
rng = random.Random(373)
np_rng = np.random.default_rng(373)
spacing = .0078
grid = defaultdict(list)
roots = []
for attempt in range(40000):
    face = faces[bisect.bisect_left(areas, rng.random()*total)]
    a, b, c = (positions[v] for v in face['v'])
    u, v = math.sqrt(rng.random()), rng.random()
    weights = (1-u, u*(1-v), u*v)
    root = a*weights[0]+b*weights[1]+c*weights[2]
    part_x = .040+.13*(root.y+.070)
    part_zone = root.z > 1.720 and -.105 < root.y < .065
    if part_zone and abs(root.x-part_x) < .0030:
        continue
    cell = tuple(math.floor(c/spacing) for c in root)
    neighbors = (p for x in range(cell[0]-1, cell[0]+2)
                 for y in range(cell[1]-1, cell[1]+2)
                 for z in range(cell[2]-1, cell[2]+2)
                 for p in grid.get((x, y, z), ()))
    if any((p-root).length_squared < spacing**2 for p in neighbors):
        continue
    grid[cell].append(root)
    roots.append((root, face, weights))
    if len(roots) == 1100:
        break

children, steps = 96, 32
t = np.linspace(0., 1., steps, dtype=np.float32)
points = np.empty((len(roots), children, steps, 3), dtype=np.float32)
radii = np.empty((len(roots), children, steps), dtype=np.float32)
uvs = np.empty((len(roots), children, 2), dtype=np.float32)
for gi, (root, face, weights) in enumerate(roots):
    normal = Vector(face['normal']).normalized()
    ellipsoid = Vector((root.x/.095**2, (root.y-.012)/.115**2, (root.z-1.682)/.118**2)).normalized()
    if normal.dot(ellipsoid) < 0:
        normal.negate()
    normal = (normal*.32+ellipsoid*.68).normalized()
    part_x = .040+.13*(root.y+.070)
    part_zone = root.z > 1.720 and -.105 < root.y < .065
    direction = Vector((-.85, .30, .05))
    if root.x > part_x and root.y < .035:
        direction = Vector((.25, .65, -.30))
    elif root.y > .035:
        direction = Vector((0., .65, -.50))
    tangent = (direction-normal*direction.dot(normal)).normalized()
    across = normal.cross(tangent).normalized()
    # Tilted axes give three-dimensional ringlets instead of flat loops
    # stamped onto the scalp. Children converge into the same curl bundle.
    axis = (normal*.78+tangent*.63+across*rng.uniform(-.15, .15)).normalized()
    curl_u = (tangent-axis*tangent.dot(axis)).normalized()
    curl_v = axis.cross(curl_u).normalized()
    topness = min(1., max(0., (root.z-1.69)/.08))
    radius = rng.uniform(.0032, .0045)*(.72+.28*topness)
    length = rng.uniform(.014, .019)*(.60+.40*topness)
    turns, phase = rng.uniform(.35, .60), rng.random()*math.tau
    if part_zone and abs(root.x-part_x) < .010:
        radius *= .75
    centerline = []
    for tj in t:
        q = float(tj)
        angle = phase+math.tau*turns*q
        growth = min(1., q*5.)
        p = root+normal*.0005+axis*(length*q)
        p += radius*growth*(curl_u*(math.cos(angle)-math.cos(phase))+curl_v*(math.sin(angle)-math.sin(phase)))
        near, n, _, _ = bvh.find_nearest(p)
        if near is not None:
            clearance = (p-near).dot(n)
            if clearance < .00055:
                p += n*(.00055-clearance)
        if part_zone and -.105 < p.y < .065:
            edge = .040+.13*(p.y+.070)
            p.x = min(p.x, edge-.0014) if root.x < part_x else max(p.x, edge+.0014)
        centerline.append(p)
    angles = np_rng.uniform(0., math.tau, children)
    widths = np.sqrt(np_rng.uniform(0., 1., children))*rng.uniform(.0022, .0028)
    offset = (np.cos(angles)[:, None]*np.asarray(tangent)+np.sin(angles)[:, None]*np.asarray(across))*widths[:, None]
    spread = .24+.76*np.exp(-5*t)
    block = np.asarray(centerline, dtype=np.float32)[None, :, :]+offset[:, None, :]*spread[None, :, None]
    phase_jitter = np_rng.uniform(-.3, .3, children)[:, None]
    amplitude = np_rng.uniform(.000015, .00010, children)[:, None]
    wave = np.sin(t[None, :]*math.tau*turns+phase_jitter)*amplitude
    block += wave[:, :, None]*np.asarray(curl_v)[None, None, :]
    for child in range(children):
        near, n, _, _ = bvh.find_nearest(Vector(block[child, 0]))
        if near is not None:
            block[child, 0] = near+n*.00008
    points[gi] = block
    root_radii = np_rng.uniform(.000028, .000043, children)
    radii[gi] = root_radii[:, None]*(1.-.78*t**2)[None, :]
    radii[gi, :, -1] = .0000025
    uvs[gi] = np.asarray(weights) @ np.asarray(face['uv'])

for obj in bpy.context.scene.objects:
    if obj.name in ('V370_CURL_GROOM', 'V371_CURL_GROOM', 'V373_CURL_GROOM'):
        obj.hide_render = True
        obj.hide_set(True)
assert bpy.data.objects.get('V375_CURL_GROOM') is None, 'Do not stack duplicate grooms'
curves = bpy.data.hair_curves.new('V375_OVERLAPPING_CURL_STRANDS')
curves.add_curves([steps]*(len(roots)*children))
curves.set_types(type='CATMULL_ROM')
curves.position_data.foreach_set('vector', points.ravel())
curves.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii.ravel())
curves.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', uvs.ravel())
curves.surface = body
curves.surface_uv_map = body.data.uv_layers.active.name
curves.surface_collision_distance = .0002
mat = bpy.data.materials.new('V375_BLACK_CURL_FIBER')
mat.use_nodes = True
mat.node_tree.nodes.clear()
output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
shader = mat.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled')
shader.model = 'HUANG'
shader.parametrization = 'MELANIN'
for name, value in {'Melanin':.99, 'Melanin Redness':.06, 'Roughness':.30,
                    'IOR':1.55, 'Aspect Ratio':.85, 'Random Color':.025,
                    'Random Roughness':.12}.items():
    shader.inputs[name].default_value = value
mat.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
mat.diffuse_color = (.003, .002, .0015, 1.)
curves.materials.append(mat)
obj = bpy.data.objects.new('V375_CURL_GROOM', curves)
bpy.context.scene.collection.objects.link(obj)
bone = rig.pose.bones['DEF-Head']
frame = rig.matrix_world @ bone.matrix @ Matrix.Translation((0, bone.bone.length, 0))
obj.parent = rig
obj.parent_type = 'BONE'
obj.parent_bone = 'DEF-Head'
obj.matrix_parent_inverse = frame.inverted()
obj.matrix_basis = Matrix.Identity(4)
obj['guide_count'] = len(roots)
obj['strand_count'] = len(roots)*children
obj['reference'] = 'head_expression_sheet_v2_face_refined.png'
curves.update_tag()
bpy.context.view_layer.update()

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = scene.render.resolution_y = 640
scene.camera.data.ortho_scale = .37
scene.camera.location = (0, -1.4, 1.66)
scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
report = {'guides':len(roots), 'strands':len(roots)*children, 'points':len(curves.points),
          'root_spacing_m':spacing, 'turns_range':[.35,.60], 'length_range_m':[.014,.019],
          'hair_shader':shader.model, 'rig_drivers':len(rig.animation_data.drivers),
          'build_seconds':time.monotonic()-started}
(OUT/'groom_report.json').write_text(json.dumps(report, indent=2))
assert len(rig.animation_data.drivers) == 1957
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_overlapping_curls_v375.blend'), compress=True)
for name, loc in [('front', (0, -1.4, 1.66)), ('threequarter', (.53, -1.25, 1.69))]:
    scene.camera.location = loc
    scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT/f'v375_{name}.png')
    bpy.ops.render.render(write_still=True)
scene.camera.location = (0, -1.4, 1.66)
scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
print(json.dumps(report))
