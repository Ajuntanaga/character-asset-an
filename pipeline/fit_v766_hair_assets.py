"""Fit finished Bystedt/Einar strands to the native face and retain UV animation."""
import json
import runpy
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
LIBRARY = Path('results/hair-library')
OUT = Path('results')
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
mesh = head.data
assert len(mesh.vertices) == 18024 and len(mesh.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
head.add_rest_position_attribute = True
coords = np.empty((len(mesh.vertices), 3), dtype=np.float32)
mesh.shape_keys.key_blocks['Basis'].data.foreach_get('co', coords.ravel())
# The native face stores anatomical coordinates in mesh space. Its object
# transform is inherited by the new child curves, rather than applied twice.
assert 1.70 < float(coords[:, 2].max()) < 1.85
original_keys = {k.name: float(k.value) for k in mesh.shape_keys.key_blocks}
mesh.calc_loop_triangles()
parts = json.loads((ROOT / 'v740_native_regions.json').read_text())['parts']
removed = set(parts['Eyes']['faces']) | set(parts['Mouth']['faces'])
kept = [i for i in range(len(mesh.polygons) + len(removed)) if i not in removed]
scalp_faces = set(parts['Scalp']['faces'])
report = {'source': bpy.data.filepath, 'grooms': {}, 'preserved_shape_keys': len(original_keys),
          'revision': 'shared donor curl guides; coherent clumps; restrained part and crown',
          'preserved_rig_drivers': len(rig.animation_data.drivers),
          'head_matrix_world': [list(row) for row in head.matrix_world],
          'head_local_bounds': [coords.min(0).tolist(), coords.max(0).tolist()],
          'license_file': 'licenses/hair-asset-sources.md'}


def unit(value):
    return value / max(float(np.linalg.norm(value)), 1e-12)


class Surface:
    def __init__(self, triangles):
        self.triangles = np.asarray([t.vertices[:] for t in triangles], dtype=np.int32)
        self.uv = np.asarray([[mesh.uv_layers['UVMap'].data[i].uv[:] for i in t.loops]
                              for t in triangles])
        self.points = coords[self.triangles].astype(np.float64)
        self.tree = BVHTree.FromPolygons(coords.tolist(), self.triangles.tolist(), all_triangles=True)
        normal = np.cross(self.points[:, 1]-self.points[:, 0], self.points[:, 2]-self.points[:, 0])
        self.vertex_normals = np.zeros(coords.shape, dtype=np.float64)
        for corner in range(3):
            np.add.at(self.vertex_normals, self.triangles[:, corner], normal)
        self.vertex_normals /= np.maximum(np.linalg.norm(self.vertex_normals, axis=1, keepdims=True), 1e-12)

    def attach(self, point, front=False):
        if front:
            hit, normal, index, distance = self.tree.ray_cast(Vector((point[0], -.6, point[2])), Vector((0, 1, 0)))
        else:
            hit, normal, index, distance = self.tree.find_nearest(Vector(point))
        if hit is None:
            return None
        if front and normal.y > -.10:
            return None
        hit = np.asarray(hit)
        a, b, c = self.points[index]
        ab, ac, ap = b-a, c-a, hit-a
        d00, d01, d11 = ab@ab, ab@ac, ac@ac
        denom = d00*d11-d01*d01
        if abs(denom) < 1e-20:
            return None
        v = (d11*(ap@ab)-d01*(ap@ac))/denom
        w = (d00*(ap@ac)-d01*(ap@ab))/denom
        bary = np.array((1-v-w, v, w))
        return hit, unit(bary @ self.vertex_normals[self.triangles[index]]), bary @ self.uv[index]


surface = Surface(list(mesh.loop_triangles))
scalp = Surface([t for t in mesh.loop_triangles if kept[t.polygon_index] in scalp_faces])


def donor(name):
    with np.load(LIBRARY / (name + '.npz')) as f:
        return {k: f[k] for k in f.files}


def donor_surface(name):
    data = donor(name)
    return BVHTree.FromPolygons(data['points'].tolist(), data['triangles'].tolist(), all_triangles=True)


def trim(path, length):
    """Cut by arc length while retaining the artist's strand curvature."""
    distances = np.r_[0., np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    if distances[-1] <= length:
        return path
    index = int(np.searchsorted(distances, length))
    fraction = (length-distances[index-1]) / max(distances[index]-distances[index-1], 1e-12)
    return np.vstack((path[:index], path[index-1]*(1-fraction)+path[index]*fraction))


def rotation(source, target):
    return np.asarray(Vector(unit(source)).rotation_difference(Vector(unit(target))).to_matrix())


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value*value*(3.-2.*value)


material = bpy.data.materials.new('V766_DARK_NATURAL_HAIR')
material.use_nodes = True
material.node_tree.nodes.clear()
shader = material.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled')
shader.model = 'CHIANG'
shader.parametrization = 'MELANIN'
for name, value in {'Melanin': .99, 'Melanin Redness': .10, 'Roughness': .27,
                    'Radial Roughness': .32, 'Coat': .12,
                    'Random Color': .03, 'Random Roughness': .10}.items():
    if name in shader.inputs:
        shader.inputs[name].default_value = value
output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
material.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
group = bpy.data.node_groups.new('V766_UV_FACIAL_HAIR_ATTACHMENT', 'GeometryNodeTree')
group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
inp = group.nodes.new('NodeGroupInput')
deform = group.nodes.new('GeometryNodeDeformCurvesOnSurface')
set_material = group.nodes.new('GeometryNodeSetMaterial')
set_material.inputs['Material'].default_value = material
out = group.nodes.new('NodeGroupOutput')
group.links.new(inp.outputs['Geometry'], deform.inputs['Curves'])
group.links.new(deform.outputs['Curves'], set_material.inputs['Geometry'])
group.links.new(set_material.outputs['Geometry'], out.inputs['Geometry'])
installed = []


def install(name, paths, uvs, radius, attribution):
    assert len(paths) > 20, (name, len(paths))
    data = bpy.data.hair_curves.new(name)
    data.add_curves([len(p) for p in paths])
    data.set_types(type='CATMULL_ROM')
    all_points = np.concatenate(paths).astype(np.float32)
    assert np.isfinite(all_points).all()
    data.position_data.foreach_set('vector', all_points.ravel())
    radii = [radius * (1.0-.94*np.linspace(0, 1, len(p))**2) for p in paths]
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', np.concatenate(radii).astype(np.float32))
    data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', np.asarray(uvs, dtype=np.float32).ravel())
    data.surface = head
    data.surface_uv_map = 'UVMap'
    data.surface_collision_distance = .00015
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = head
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = Matrix.Identity(4)
    obj.modifiers.new('Follow native face and FACS', 'NODES').node_group = group
    obj['asset_source_and_license'] = attribution
    obj['adaptation'] = 'Donor guides adapted with coherent children; native UV roots retained; cropped and recolored'
    obj.hide_set(True)
    obj.hide_render = True
    installed.append(obj.name)
    report['grooms'][name] = {'strands': len(paths), 'points': len(all_points),
                              'bounds': [all_points.min(0).tolist(), all_points.max(0).tolist()],
                              'surface': head.name, 'radius_m': radius, 'attribution': attribution}
    print('FITTED_HAIR', name, len(paths), flush=True)


data = donor('bystedt_curls')
starts, ends = data['offsets'][:-1], data['offsets'][1:]
assert np.all(ends-starts == 23), 'The finished donor curls must share a sample count'
source_paths = data['points'].reshape(-1, 23, 3).astype(np.float64)
source_delta = source_paths-source_paths[:, :1]
arc_lengths = np.linalg.norm(np.diff(source_paths, axis=1), axis=2).sum(axis=1)
restore = runpy.run_path(str(ROOT / 'native_cranium_mapping.py'))['restore_upper_head']
attached_roots, source_ids = [], []
scalp_rejected = 0
for source_id, root in enumerate(source_paths[:, 0]):
    guess = (root-np.array((10., -.60, 15.30)))*np.array((.105, .11, .080))+np.array((0., -.015, 1.665))
    attached = scalp.attach(guess)
    if attached is None:
        scalp_rejected += 1
        continue
    p, normal, uv = attached
    front = 1.703-.060*smooth((abs(p[0])-.052)/.041)
    transition = smooth((p[1]+.050)/.080)
    hairline = float(restore(front*(1-transition)+1.595*transition))
    part_x = .041+.13*(p[1]+.065)
    in_part = p[2] > 1.690 and -.09 < p[1] < .05 and abs(p[0]-part_x) < .0013
    if p[2] < hairline or in_part:
        scalp_rejected += 1
        continue
    attached_roots.append(attached)
    source_ids.append(source_id)

# Choose spatially separated real donor curls as guides. All child fibers in a
# group follow the SAME curl phase, axis and scale. Averaging just the chord
# still left independent curl phases crossing into a woolly mass in V765.
root_positions = np.asarray([item[0] for item in attached_roots])
source_ids = np.asarray(source_ids)
part_sides = root_positions[:, 0]-(.041+.13*(root_positions[:, 1]+.065)) >= 0
assignments = np.full(len(root_positions), -1, dtype=np.int32)
guide_ids = []
for side in (False, True):
    ids = np.flatnonzero(part_sides == side)
    positions = root_positions[ids]
    nearest_distance = np.full(len(ids), np.inf)
    chosen = int(np.argmax(positions[:, 2]))
    while True:
        guide_id = int(ids[chosen])
        distance = np.sum((positions-positions[chosen])**2, axis=1)
        closer = distance < nearest_distance
        nearest_distance[closer] = distance[closer]
        assignments[ids[closer]] = guide_id
        guide_ids.append(guide_id)
        chosen = int(np.argmax(nearest_distance))
        if nearest_distance[chosen] <= .0065**2:
            break
assert np.all(assignments >= 0)
assert np.all(part_sides == part_sides[assignments]), 'Clumps must not cross the part'

transports = {}
for guide_id in guide_ids:
    p, normal, uv = attached_roots[guide_id]
    donor_id = source_ids[guide_id]
    top = float(smooth((p[2]-1.685)/.055))
    desired_length = .018+.052*top
    signed_part_distance = p[0]-(.041+.13*(p[1]+.065))
    side = -1. if signed_part_distance < 0 else 1.
    across_part = np.array((1., -.13, 0.))
    across_part = unit(across_part-normal*(across_part@normal))
    back = np.array((0., 1., 0.))
    back -= normal*(back@normal)
    part_flow = .20+.30*np.exp(-abs(signed_part_distance)/.014)*top
    direction = unit(normal+side*part_flow*across_part+.15*back)
    rotate = rotation(source_delta[donor_id, -1], direction)
    transports[guide_id] = (rotate, desired_length/arc_lengths[donor_id])

paths, uvs = [], []
max_root_displacement = 0.
t = np.linspace(0., 1., 23)
# Roots remain at their own UVs; the bundle gathers over its first half rather
# than teleporting every root onto a guide. Keep a small natural residual.
root_spread = (1.-.80*smooth(t/.50))[:, None]
residual_weight = (.06*smooth(t/.25))[:, None]
for child_id, (p, normal, uv) in enumerate(attached_roots):
    guide_id = int(assignments[child_id])
    guide_p = root_positions[guide_id]
    child_source, guide_source = source_ids[child_id], source_ids[guide_id]
    rotate, scale = transports[guide_id]
    guide_delta = source_delta[guide_source]
    child_delta = source_delta[child_source]*(arc_lengths[guide_source]/arc_lengths[child_source])
    delta = guide_delta+residual_weight*(child_delta-guide_delta)
    path = guide_p+(delta @ rotate.T)*scale+root_spread*(p-guide_p)
    assert np.linalg.norm(path[0]-p) < 1e-8
    for index, point in enumerate(path):
        hit, n, _, distance = scalp.tree.find_nearest(Vector(point))
        if hit is not None:
            clearance = (Vector(point)-hit).dot(n)
            if clearance < .00012:
                path[index] += np.asarray(n)*(.00012-clearance)
    tangent = unit(np.cross(normal, np.array((0., 0., 1.))))
    for offset in (-.00012, 0., .00012):
        sibling = scalp.attach(p+tangent*offset)
        if sibling is None:
            continue
        sibling_root, _, sibling_uv = sibling
        max_root_displacement = max(max_root_displacement, float(np.linalg.norm(path[0]-p)))
        paths.append(path+sibling_root-p)
        uvs.append(sibling_uv)
install('V766_ASSET_SCALP', paths, uvs, .000045,
        'Daniel Bystedt - Hair Styles - CC BY-SA; adapted curly groom')
report['scalp_rejected_outside_reference_hairline'] = scalp_rejected
report['scalp_transport'] = {
    'guide_count': len(guide_ids), 'guide_coverage_radius_m': .0065,
    'shared_curve_phase_direction_and_scale': True, 'child_shape_residual': .06,
    'tip_root_spread_fraction': .20, 'root_part_width_m': .0026,
    'side_arc_length_m': .018, 'crown_arc_length_m': .070,
    'root_attachment_max_displacement_m': max_root_displacement,
    'guide_member_counts': [int(np.count_nonzero(assignments == i)) for i in guide_ids],
}


einar_tree = donor_surface('einar_head')
for kind, source_parts, radius in [
    ('BROWS', ('eyebrows',), .000035),
    ('BEARD', ('beard', 'beard.messy'), .000042),
    ('MUSTACHE', ('mustache', 'mustache.messy'), .000038),
    ('LASHES', ('eyelashes',), .000023),
]:
    paths, uvs = [], []
    rejected = 0
    for part in source_parts:
        data = donor('einar_' + part)
        for first, last in zip(data['offsets'][:-1], data['offsets'][1:]):
            source = data['points'][first:last].astype(np.float64)
            root = source[0]
            guess = root.copy()
            if kind == 'BROWS':
                guess[0] *= 1.02
                guess[2] = 1.664 + (root[2]-1.687)*.70
                length = .0060
            elif kind == 'LASHES':
                guess[0] *= 1.38
                guess[2] = 1.649 + (root[2]-1.673)*1.50
                length = .0026
            elif kind == 'MUSTACHE':
                guess[0] *= .70
                guess[2] = 1.585 + (root[2]-1.621)*.65
                length = .0040
            else:
                guess[0] *= .96
                guess[2] = float(np.interp(root[2], [1.50, 1.56, 1.61, 1.67], [1.520, 1.545, 1.580, 1.635]))
                length = .0020 + .0020*(1-smooth((guess[2]-1.54)/.06))
            attached = surface.attach(guess, front=True)
            if attached is None:
                rejected += 1
                continue
            p, normal, uv = attached
            if kind == 'BEARD':
                lateral = abs(p[0])
                edge = float(np.interp(lateral, [.0, .025, .035, .050, .080], [1.562, 1.565, 1.585, 1.609, 1.640]))
                if p[2] > edge or p[2] < 1.513:
                    rejected += 1
                    continue
            elif kind == 'MUSTACHE':
                if p[2] < 1.578 or p[2] > 1.599 or (p[2] > 1.590 and abs(p[0]) < .020):
                    rejected += 1
                    continue
            _, donor_normal, _, _ = einar_tree.find_nearest(Vector(root))
            if donor_normal is None:
                continue
            rotate = rotation(np.asarray(donor_normal), normal)
            path = trim(p + ((source-root)*.80) @ rotate.T, length)
            # Facial fibers are short: keep tips above the local skin tangent.
            clearance = (path-p) @ normal
            path += np.maximum(.00008-clearance, 0)[:, None]*normal
            paths.append(path)
            uvs.append(uv)
    install('V766_ASSET_' + kind, paths, uvs, radius,
            'Einar Rig (CC-BY 4.0) Blender Foundation | studio.blender.org; adapted ' + kind.lower())
    report['grooms']['V766_ASSET_' + kind]['rejected'] = rejected


old_names = ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']
for name in old_names:
    bpy.data.objects[name].hide_render = True
    bpy.data.objects[name].hide_set(True)
inspection = bpy.data.scenes['V739_NATIVE_FACE_INSPECTION']
for name in installed + [head.name]:
    obj = bpy.data.objects[name]
    if name not in inspection.objects:
        inspection.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    for layer in inspection.view_layers:
        if name in layer.objects:
            obj.hide_set(False, view_layer=layer)
notice = bpy.data.texts.new('V766_LICENSED_HAIR_SOURCES')
notice.write((ROOT.parent / 'licenses/hair-asset-sources.md').read_text())
assert {k.name: float(k.value) for k in mesh.shape_keys.key_blocks} == original_keys
bpy.context.view_layer.update()
report['installed_objects'] = installed
report['evaluated_materials'] = {}
depsgraph = bpy.context.evaluated_depsgraph_get()
for name in installed:
    evaluated = bpy.data.objects[name].evaluated_get(depsgraph)
    materials = [m.name if m else None for m in evaluated.data.materials]
    assert material.name in materials, (name, materials)
    report['evaluated_materials'][name] = materials
(OUT / 'v766_hair_fit.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V766_licensed_hair_trial.blend').resolve()), compress=True)

camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': installed, 'EXCLUDE_OBJECTS': old_names,
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
    **base, 'TAG': 'v766_asset_hair', 'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera})
runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
    **base, 'TAG': 'v766_asset_hair_front', 'VIEWS': ['front']})
runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
    **base, 'TAG': 'v766_asset_hair_motion', 'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera,
    'HEAD_TURN_DEGREES': 12., 'POSE': {'Blink.L': .65, 'Blink.R': .65}})
print('ASSET_HAIR_TRIAL_COMPLETE', installed, flush=True)
