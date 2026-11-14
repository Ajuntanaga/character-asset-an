"""Reconstruct the native groom from the isolated V739 checkpoint on a cloud runner."""
import bpy
import json
import math
import os
import heapq
import runpy
from collections import defaultdict
from pathlib import Path

import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
restore_upper_head = runpy.run_path(str(ROOT/'native_cranium_mapping.py'))['restore_upper_head']
OUT = Path('results')
OUT.mkdir(exist_ok=True)
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
source = bpy.data.objects['V739_NATIVE_FACE']
assert len(source.data.vertices) == 18024
assert len(source.data.shape_keys.key_blocks) == 52
production = bpy.data.filepath
assert len(rig.animation_data.drivers) == 1957
assert not bpy.app.is_job_running('RENDER')
assert 'V740_NATIVE_FACE' not in bpy.data.objects
assert all(abs(k.value) < 1e-6 for k in source.data.shape_keys.key_blocks)
head = source.copy()
head.data = source.data.copy()
head.name = 'V740_NATIVE_FACE'
bpy.context.scene.collection.objects.link(head)
head.hide_set(True)
head.hide_render = True
head.add_rest_position_attribute = True
for mod in head.modifiers:
    if mod.type == 'SUBSURF':
        mod.uv_smooth = 'NONE'
# Apply the same monotone field to Basis and all native expression keys.
# Groom roots are rebuilt below on the corrected surface, preserving native UVs.
for key in head.data.shape_keys.key_blocks:
    coords = np.empty((len(head.data.vertices), 3), dtype=np.float32)
    key.data.foreach_get('co', coords.ravel())
    coords[:, 2] = restore_upper_head(coords[:, 2])
    key.data.foreach_set('co', coords.ravel())
co = np.empty((len(head.data.vertices), 3), dtype=np.float32)
head.data.shape_keys.key_blocks['Basis'].data.foreach_get('co', co.ravel())
head.data.vertices.foreach_set('co', co.ravel())
head.data.update()
parts = json.loads((ROOT/'v740_native_regions.json').read_text())['parts']
removed = set(parts['Eyes']['faces']) | set(parts['Mouth']['faces'])
scalp_faces = set(parts['Scalp']['faces'])
neck_faces = set(parts['NeckLower']['faces']) | set(parts['NeckUpper']['faces'])
# V737 retained all vertex IDs and emitted surviving polygons in source order.
original_face_count = len(head.data.polygons) + len(removed)
assert all(0 <= i < original_face_count for i in removed | scalp_faces | neck_faces)
kept = [i for i in range(original_face_count) if i not in removed]
assert len(kept) == len(head.data.polygons)

# Feather the clean scalp/nape into the photo material on the native mesh.
# Point-domain weights follow all FACS keys; no camera-dependent mask or hard
# polygon material boundary is introduced. Preserve the atlas in observed skin.
clean_faces = set()
assigned = {'scalp': 0, 'rear_neck': 0}
for polygon, original in zip(head.data.polygons, kept):
    region = 'scalp' if original in scalp_faces else 'rear_neck' if original in neck_faces and co[list(polygon.vertices), 1].mean() > 0 else None
    if region:
        clean_faces.add(polygon.index)
        assigned[region] += 1
incident = [set() for _ in co]
for polygon in head.data.polygons:
    for vertex in polygon.vertices:
        incident[vertex].add(polygon.index in clean_faces)
inside = np.array([True in flags for flags in incident])
boundary = [i for i, flags in enumerate(incident) if len(flags) == 2]
assert boundary, 'Clean skin transition has no boundary'
adjacency = [[] for _ in co]
for edge in head.data.edges:
    a, b = edge.vertices
    distance = float(np.linalg.norm(co[a]-co[b]))
    adjacency[a].append((b, distance))
    adjacency[b].append((a, distance))
distances = np.full(len(co), np.inf)
queue = [(0.0, i) for i in boundary]
for i in boundary:
    distances[i] = 0.0
heapq.heapify(queue)
feather = .008
while queue:
    distance, i = heapq.heappop(queue)
    if distance != distances[i] or distance > feather:
        continue
    for j, length in adjacency[i]:
        candidate = distance+length
        if candidate < distances[j] and candidate <= feather:
            distances[j] = candidate
            heapq.heappush(queue, (candidate, j))
signed = np.where(inside, distances, -distances)
weights = np.clip(.5+signed/(2*feather), 0, 1)
weights = weights*weights*(3-2*weights)
# The reference atlas contains clothing/background wedges on the lower neck.
# Fade below the jaw in rest coordinates; the point attribute follows FACS.
# Complete the fade above the atlas edge visible in the bilateral review.
neck_fade_top, neck_fade_bottom = 1.555, 1.520
lower_neck = np.clip((neck_fade_top-co[:, 2])/(neck_fade_top-neck_fade_bottom), 0, 1)
lower_neck = lower_neck*lower_neck*(3-2*lower_neck)
weights = np.maximum(weights, lower_neck)
assert np.isfinite(weights).all() and weights.min() >= 0 and weights.max() <= 1
attribute = head.data.attributes.new('V740_CleanSkinBlend', 'FLOAT', 'POINT')
attribute.data.foreach_set('value', weights.astype(np.float32))
skin = bpy.data.materials['V736_NATIVE_PHOTO_SKIN'].copy()
skin.name = 'V740_FEATHERED_NATIVE_SKIN'
nodes, links = skin.node_tree.nodes, skin.node_tree.links
shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
# The imported photo material has IOR 1.0, suppressing dielectric reflection.
source_skin_ior = float(shader.inputs['IOR'].default_value)
shader.inputs['IOR'].default_value = 1.4
assert shader.inputs['Base Color'].is_linked
photo = shader.inputs['Base Color'].links[0].from_socket
# Rest coordinates keep procedural skin detail attached during facial animation.
rest_skin = head.data.attributes.new('V740_SkinRestPosition', 'FLOAT_VECTOR', 'POINT')
rest_skin.data.foreach_set('vector', co.astype(np.float32).ravel())
rest_node = nodes.new('ShaderNodeAttribute')
rest_node.attribute_name = rest_skin.name
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 25
noise.inputs['Detail'].default_value = 2
links.new(rest_node.outputs['Vector'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (.22, .10, .047, 1)
ramp.color_ramp.elements[1].color = (.30, .148, .078, 1)
links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
mask = nodes.new('ShaderNodeAttribute')
mask.attribute_name = attribute.name
mix = nodes.new('ShaderNodeMixRGB')
links.new(mask.outputs['Fac'], mix.inputs[0])
links.new(photo, mix.inputs[1])
links.new(ramp.outputs['Color'], mix.inputs[2])
links.new(mix.outputs['Color'], shader.inputs['Base Color'])
pores = nodes.new('ShaderNodeTexNoise')
pores.name = 'V740_CleanSkinMicrodetail'
pores.inputs['Scale'].default_value = 1400.
pores.inputs['Detail'].default_value = 2.
links.new(rest_node.outputs['Vector'], pores.inputs['Vector'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Distance'].default_value = .00004
strength = nodes.new('ShaderNodeMath')
strength.operation = 'MULTIPLY'
strength.inputs[1].default_value = .25
links.new(mask.outputs['Fac'], strength.inputs[0])
links.new(strength.outputs[0], bump.inputs['Strength'])
links.new(pores.outputs['Fac'], bump.inputs['Height'])
if shader.inputs['Normal'].is_linked:
    links.new(shader.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
links.new(bump.outputs['Normal'], shader.inputs['Normal'])
head.data.materials.clear()
head.data.materials.append(skin)
for polygon in head.data.polygons:
    polygon.material_index = 0

photo_repair = runpy.run_path(str(ROOT/'repair_v740_photo_coverage.py'))['repair_photo_coverage'](head, skin, co)

head.data.calc_loop_triangles()
scalp_triangles = [t for t in head.data.loop_triangles if kept[t.polygon_index] in scalp_faces]
assert scalp_triangles, 'Semantic scalp selection is empty'
triangles = np.array([t.vertices[:] for t in scalp_triangles], dtype=np.int32)
uv = np.array([[head.data.uv_layers['UVMap'].data[i].uv[:] for i in t.loops] for t in scalp_triangles])
tc = co[triangles]
cross = np.cross(tc[:, 1]-tc[:, 0], tc[:, 2]-tc[:, 0])
areas = np.linalg.norm(cross, axis=1)*.5
tri_normals = cross/np.maximum(2*areas[:, None], 1e-12)
cumulative = np.cumsum(areas)
scalp = BVHTree.FromPolygons([Vector(p) for p in co], triangles.tolist(), all_triangles=True)
rng = np.random.default_rng(740)

def unit(v):
    return v/max(np.linalg.norm(v), 1e-12)

def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)

part_height = float(restore_upper_head(1.687))
top_start = float(restore_upper_head(1.678))
top_span = float(restore_upper_head(1.728)) - top_start

def in_part(p):
    return p[2] > part_height and -.080 < p[1] < .050 and abs(p[0]-(.041+.13*(p[1]+.065))) < .0016

def crosses_part(path, surface_clearance=None):
    """Protect the scalp part without cutting a vertical void through raised curls."""
    # Check segment midpoints too, including short undercoat segments.
    points = np.concatenate((path, (path[:-1]+path[1:])*.5))
    active = (points[:, 2] > part_height) & (points[:, 1] > -.080) & (points[:, 1] < .050)
    bank = 1. if path[0, 0]-(.041+.13*(path[0, 1]+.065)) >= 0 else -1.
    distance = bank*(points[:, 0]-(.041+.13*(points[:, 1]+.065)))
    candidates = points[active & (distance < .0016)]
    if surface_clearance is None:
        return bool(len(candidates))
    # V33: the part is a scalp feature. Whole-lock rejection at every height
    # removes roots well outside its 3.2 mm width when a raised curl overlaps it.
    # Keep near-surface crossings excluded, but allow elevated curl overlap.
    for point in candidates:
        hit, normal, _, _ = scalp.find_nearest(Vector(point))
        if hit is None or (Vector(point)-hit).dot(normal) < surface_clearance:
            return True
    return False

part_rejections = {'curl': 0, 'undercoat': 0}

hairline_levels = np.linspace(1.590, 1.710, 4097)
restored_hairline_levels = restore_upper_head(hairline_levels)

def hairline_margin(p):
    front = 1.703-.060*smooth((abs(p[0])-.052)/.041)
    transition = smooth((p[1]+.050)/.080)
    limit = front*(1-transition)+1.595*transition
    return p[2] - float(np.interp(limit, hairline_levels, restored_hairline_levels))

def allowed(p):
    return hairline_margin(p) > 0 and not in_part(p)

def sample():
    index = min(len(triangles)-1, int(np.searchsorted(cumulative, rng.random()*cumulative[-1])))
    a, b = rng.random(2)
    if a+b > 1:
        a, b = 1-a, 1-b
    bary = np.array([1-a-b, a, b])
    return bary@tc[index], tri_normals[index], bary@uv[index]

def attachment(q):
    p, normal, index, _ = scalp.find_nearest(Vector(q))
    if p is None:
        return None
    a, b, c = tc[index]
    v0, v1, v2 = b-a, c-a, np.array(p)-a
    d00, d01, d11 = v0@v0, v0@v1, v1@v1
    denom = d00*d11-d01*d01
    if abs(denom) < 1e-20:
        return None
    v = (d11*(v2@v0)-d01*(v2@v1))/denom
    w = (d00*(v2@v1)-d01*(v2@v0))/denom
    return np.array(p), np.array(normal), np.array([1-v-w, v, w])@uv[index]

guides, grid = [], defaultdict(list)
# Retain V17 coverage while correcting crown lock orientation and height.
spacing = .0056
for _ in range(24000):
    p, n, root_uv = sample()
    if not allowed(p):
        continue
    cell = tuple(np.floor(p/spacing).astype(int))
    nearby = [q for dx in (-1,0,1) for dy in (-1,0,1) for dz in (-1,0,1)
              for q in grid[(cell[0]+dx, cell[1]+dy, cell[2]+dz)]]
    if any(np.linalg.norm(q-p) < spacing for q in nearby):
        continue
    grid[cell].append(p)
    guides.append((p, n, root_uv))

mat = bpy.data.materials.new('V740_BLACK_RINGLET_FIBERS')
mat.use_nodes = True
mat.node_tree.nodes.clear()
hair = mat.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled')
hair.parametrization = 'MELANIN'
output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
mat.node_tree.links.new(hair.outputs[0], output.inputs['Surface'])
for name, value in {'Melanin': .985, 'Roughness': .52, 'Radial Roughness': .48,
                    'Random Color': .06, 'Random Roughness': .10}.items():
    if name in hair.inputs:
        hair.inputs[name].default_value = value

group = bpy.data.node_groups.new('V740_NATIVE_SURFACE_DEFORMATION', 'GeometryNodeTree')
group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
input_node = group.nodes.new('NodeGroupInput')
deform = group.nodes.new('GeometryNodeDeformCurvesOnSurface')
output_node = group.nodes.new('NodeGroupOutput')
group.links.new(input_node.outputs['Geometry'], deform.inputs['Curves'])
group.links.new(deform.outputs['Curves'], output_node.inputs['Geometry'])

def install(name, paths, widths, uvs):
    data = bpy.data.hair_curves.new(name)
    data.add_curves([len(path) for path in paths])
    data.set_types(type='CATMULL_ROM')
    data.position_data.foreach_set('vector', np.concatenate(paths).astype(np.float32).ravel())
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', np.concatenate(widths).astype(np.float32))
    data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', np.asarray(uvs, dtype=np.float32).ravel())
    data.surface = head
    data.surface_uv_map = 'UVMap'
    data.surface_collision_distance = .0002
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = head
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = Matrix.Identity(4)
    obj.modifiers.new('Native FACS surface attachment', 'NODES').node_group = group
    obj.hide_set(True)
    obj.hide_render = True
    obj['attachment'] = 'Native UVMap barycentric roots; surface parent; Deform Curves on Surface'
    return obj

t = np.linspace(0, 1, 44)
emerge, bundle = smooth(t/.20), smooth(t/.30)
strands, radii, uvs = [], [], []
corrections, max_correction = 0, 0.
# Separate stream keeps guide placement and previous variation comparable.
length_rng = np.random.default_rng(74012)
shape_rng = np.random.default_rng(74031)
for p, n, root_uv in guides:
    top = float(smooth((p[2]-top_start)/top_span))
    # The front fringe curls outward and forward; sides sweep back from the part.
    forward = -.48 if p[1] < -.040 and p[2] > part_height else .75
    # Direct both banks away from the diagonal part; inward flow can fill the gap.
    part_x = .041+.13*(p[1]+.065)
    flow = np.array([.75*np.sign(p[0]-part_x)*top, forward, -.58*(1-top)])
    tangent = unit(flow-n*np.dot(flow, n))
    # V17 reads as flat linked rings. The reference crown has raised,
    # overlapping locks; lift crown axes while retaining side/back flow.
    # V31: resolved V30 locks read as repeated flat concentric discs.
    # Vary the lock plane with a separate stream, preserving root sampling.
    lateral = unit(np.cross(n, tangent))
    tilt = shape_rng.uniform(-.45, .45)
    lift = shape_rng.uniform(.55, 1.05)
    axis = unit(tangent*.90+lateral*tilt+n*(.12+lift*top))
    u = unit(n-axis*np.dot(n, axis))
    v = unit(np.cross(axis, u))
    root_u, root_v = tangent, unit(np.cross(n, tangent))
    # Keep axial travel short so locks form rounded curls rather than pointed tufts.
    # v15 isolated render leaves separated tiny locks. Increase curl extent
    # without adding strands or changing the shader; review silhouette remotely.
    # V21 reference-side review: side locks remain tiny wire loops.
    # Increase side radius by 1.5 mm, smoothly retaining the crown radius.
    radius = 1.45*(rng.uniform(.0014, .0020)+top*.00175)+.0015*(1-top)
    # Resolved curl review (43470719530): long crown travel and the added
    # arch create upright hollow loops instead of the reference ringlets.
    # Shorten crown pitch; preserve side curls, roots and random placement.
    # Resolved trial 43475854967 still has open loops. Compress crown
    # travel to 3-6 mm and add half a turn for overlapping ringlets.
    length = rng.uniform(.005, .010)*(1-.40*top)
    turns = rng.uniform(1.10, 1.65)+.50*top
    phase = rng.uniform(-math.pi, math.pi)
    theta = phase+math.tau*turns*(t+.10*np.sin(math.pi*t))
    # A smooth varying radius breaks concentric turns without adding
    # high-frequency kinks. All children share their guide's deformation.
    shape_phase = shape_rng.uniform(-math.pi, math.pi)
    radius_variation = 1.+.22*np.sin(math.tau*1.25*t+shape_phase)*np.sin(math.pi*t)
    curl_envelope = emerge*(1-.15*t)*radius_variation
    helix = radius*curl_envelope[:, None]*(
        .80*np.cos(theta)[:, None]*u+np.sin(theta)[:, None]*v)
    sweep = tangent*(.002*top*np.sin(math.pi*t))[:, None]
    # v16 clips the lower half of the .80-radius helix onto the scalp.
    # Lift the centerline beyond its normal excursion to retain rounded locks.
    guide = (p+n*(.00016+(radius*.95+.0006)*emerge[:, None])
             +axis*length*t[:, None]+sweep+helix)
    for j in range(1, len(t)):
        hit, normal, _, _ = scalp.find_nearest(Vector(guide[j]))
        if hit is not None:
            signed = (Vector(guide[j])-hit).dot(normal)
            if signed < .0006:
                shift = .0006-signed
                guide[j] += np.array(normal)*shift
                corrections += 1
                max_correction = max(max_correction, shift)
    # Keep bundle width radial to the curl instead of a fixed world-facing ribbon.
    curl_radial = .80*np.cos(theta)[:, None]*u+np.sin(theta)[:, None]*v
    curl_radial /= np.linalg.norm(curl_radial, axis=1)[:, None]
    # V32: bundle offsets belong in the plane normal to the strand path.
    # Using the helix axis here kept both offsets in the curl plane,
    # spreading the children into the concentric discs visible in V31.
    path_tangent = np.gradient(guide, axis=0)
    path_tangent /= np.linalg.norm(path_tangent, axis=1)[:, None]
    curl_radial -= path_tangent*np.sum(curl_radial*path_tangent, axis=1)[:, None]
    curl_radial /= np.linalg.norm(curl_radial, axis=1)[:, None]
    curl_binormal = np.cross(path_tangent, curl_radial)
    curl_binormal /= np.linalg.norm(curl_binormal, axis=1)[:, None]
    for _ in range(96):
        angle, radial = rng.random()*math.tau, math.sqrt(rng.random())
        root_offset = radial*.0017*(math.cos(angle)*root_u+math.sin(angle)*root_v)
        hit = attachment(p+root_offset)
        if hit is None or not allowed(hit[0]):
            continue
        q, normal, child_uv = hit
        q += normal*.00016
        # V26: round the bundle cross-section; V25 renders as flat ribbons.
        # Guide paths and strand count stay unchanged.
        packed_scale = rng.uniform(2./3., 1.)
        packed = radial*packed_scale*(.0014*math.cos(angle)*curl_binormal
                                     +.0014*math.sin(angle)*curl_radial)
        # V27: V26 isolated curls remain a thin open lattice. Preserve distal
        # bundle volume; individual fibers still taper and have staggered ends.
        clump_width = bundle*(1-.30*smooth((t-.35)/.65))
        path = guide+(q-guide[0])[None, :]*(1-bundle[:, None])+packed*clump_width[:, None]
        # Preserve phase coherence, guide spacing, count and root spread.
        child_theta = theta + rng.uniform(-.10, .10)*emerge
        # Keep children in a coherent lock; broad annular radii fill a disc.
        child_radius = radius*rng.uniform(.90, 1.10)
        child_helix = child_radius*curl_envelope[:, None]*(
            .80*np.cos(child_theta)[:, None]*u+np.sin(child_theta)[:, None]*v)
        path += (child_helix-helix)*bundle[:, None]
        irregularity = rng.uniform(.00006, .00014)*np.sin(
            math.tau*rng.uniform(3., 5.)*t+rng.uniform(-math.pi, math.pi))
        path += u*(irregularity*np.sin(math.pi*t))[:, None]
        # V28: keep fibers through at least 85% of the lock. V27 loses
        # distal coverage as children terminate from 55% onward. Retain
        # staggered tips and the same fiber count; interpolation preserves roots.
        end_fraction = float(length_rng.uniform(.85, 1.0))
        path = np.column_stack([np.interp(t*end_fraction, t, path[:, axis_index])
                                for axis_index in range(3)])
        width = rng.uniform(.000030, .000043)
        taper = np.maximum(.04, (1-t)/.15)*np.minimum(1., 1-.08*t)
        taper[t < .85] = 1-.08*t[t < .85]
        if crosses_part(path, surface_clearance=.002):
            part_rejections['curl'] += 1
            continue
        strands.append(path)
        radii.append(width*taper)
        uvs.append(child_uv)
curl = install('V740_NATIVE_CURLS', strands, radii, uvs)
curl_count = len(strands)
del strands, radii, uvs

strands, radii, uvs = [], [], []
# Opt-in until the isolated remote comparison is reviewed. Separate RNG keeps
# the existing strand sampling sequence unchanged when the trial is disabled.
undercoat_feather_mm = float(os.environ.get("UNDERCOAT_FEATHER_MM", "0"))
assert 0 <= undercoat_feather_mm <= 10
edge_rng = np.random.default_rng(74022)
edge_rejections = 0
t = np.linspace(0, 1, 16)
for _ in range(375000):
    if len(strands) == 120000:
        break
    p, n, root_uv = sample()
    if not allowed(p):
        continue
    edge_weight = (float(smooth(hairline_margin(p)/(undercoat_feather_mm*.001)))
                   if undercoat_feather_mm else 1.)
    if edge_weight < 1 and edge_rng.random() >= edge_weight:
        edge_rejections += 1
        continue
    tangent = unit(np.cross(n, [1, .3, .1]))
    across = unit(np.cross(n, tangent))
    angle = rng.uniform(-math.pi, math.pi)
    direction = tangent*math.cos(angle)+across*math.sin(angle)
    # Overlapping curved fibers fill the space below the curl bundles.
    # Keep the same surface-bound roots; this is hair, not a dark scalp mask.
    length = rng.uniform(.010, .016)*(.25+.75*edge_weight)
    lateral = unit(np.cross(n, direction))
    bend = rng.uniform(-.0025, .0025)
    # Follow scalp curvature instead of letting tangent-plane paths rise away
    # from the head. This filling layer must stay below the visible curl locks.
    lift = .0003+.0015*np.sin(math.pi*t)
    path = (p+direction*length*t[:, None]
            +lateral*bend*np.sin(math.pi*t)[:, None])
    path[0] = p+n*.00016
    for j in range(1, len(t)):
        hit, normal, _, _ = scalp.find_nearest(Vector(path[j]))
        if hit is not None:
            path[j] = np.array(hit)+np.array(normal)*lift[j]
    if crosses_part(path):
        part_rejections['undercoat'] += 1
        continue
    strands.append(path)
    radii.append(rng.uniform(.000035, .000050)*np.maximum(.06, 1-t*t))
    uvs.append(root_uv)
undercoat = install('V740_NATIVE_UNDERCOAT', strands, radii, uvs)
head.update_tag(refresh={'DATA'})
bpy.context.view_layer.update()
report = {'head': head.name, 'head_keys': len(head.data.shape_keys.key_blocks),
          'clean_material_faces': assigned, 'guide_count': len(guides),
          'curl_fibers': curl_count, 'undercoat_fibers': len(strands),
          'guide_collision_corrections': corrections, 'max_correction_mm': max_correction*1000,
          'native_uv_roots': True, 'deform_curves_on_surface': True,
          'rig_drivers': len(rig.animation_data.drivers), 'production_unchanged': production == bpy.data.filepath,
          'revision': 'surface_limited_curl_part_v33',
          'curl_part_surface_clearance_mm': 2.,
          'part_path_rejections': part_rejections,
          'cranial_mapping': {'start_z': 1.665, 'old_reduction_m': .055,
                              'trial_reduction_m': .035, 'all_shape_keys': True},
          'photo_coverage_repair': photo_repair,
          'skin_surface_ior': float(shader.inputs['IOR'].default_value),
          'source_skin_surface_ior': source_skin_ior,
          'skin_transition_half_width_mm': feather*1000,
          'lower_neck_clean_fade_z': [neck_fade_bottom, neck_fade_top],
          'clean_skin_microdetail': {'scale_per_meter': 1400, 'distance_m': .00004,
                                    'strength': .25, 'coordinates': 'rest_point_attribute'},
          'lower_neck_blended_vertices': int(np.count_nonzero(lower_neck)),
          'skin_transition_vertices': int(((weights > 0) & (weights < 1)).sum()),
          'undercoat_hairline_feather_mm': undercoat_feather_mm,
          'undercoat_edge_rejections': edge_rejections,
          'undercoat_edge_length_scale': [.25, 1.],
          'undercoat_length_mm': [10, 16], 'undercoat_target': 120000,
          'undercoat_surface_following': True, 'undercoat_max_lift_mm': 1.8,
          'undercoat_tip_lift_mm': .3,
          'undercoat_radius_microns': [35, 50],
          'children_per_guide': 96, 'guide_spacing_mm': 5.6, 'hair_roughness': .52,
          'crown_axial_length_mm': [3., 6.],
          'crown_extra_arch_mm': 0.,
          'axis_lateral_variation': [-.45, .45],
          'crown_axis_normal_coefficient': [.67, 1.17],
          'curl_radius_modulation_amplitude': .22,
          'curl_radius_modulation_cycles': 1.25,
          'side_curl_turns': [1.10, 1.65], 'crown_curl_turns': [1.60, 2.15],
          'curl_normal_flattening': .80,
          'curl_tip_clump_fraction': .70,
          'child_phase_offset_radians': [-.10, .10],
          'child_radius_scale': [.90, 1.10],
          'child_radius_distribution': 'uniform_coherent_lock',
          'child_bundle_half_axes_mm': [1.4, 1.4],
          'child_bundle_frame': 'path_normal_radial_binormal',
          'child_bundle_scale': [2./3., 1.],
          'child_length_fraction': [.85, 1.0],
          'curl_radius_scale_from_v15': 1.45,
          'side_curl_radius_addition_mm': 1.5,
          'side_curl_radius_mm': [3.53, 4.40],
          'curl_centerline_lift_radius_factor': .95,
          'crown_curl_radius_mm': [4.5675, 5.4375], 'part_flow': 'outward',
          'status': 'unreviewed_groom_trial'}
(OUT/'groom_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))

# Preserve the trial before rendering; no need to keep a live workstation scene.
scene = bpy.data.scenes['V739_NATIVE_FACE_INSPECTION']
for obj in (head, curl, undercoat):
    if obj.name not in scene.objects:
        scene.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_set(False)
source.hide_render = True
source.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'V740_cloud_groom_trial.blend').resolve()), compress=True)
