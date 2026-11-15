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


material = bpy.data.materials.new('V764_DARK_NATURAL_HAIR')
material.use_nodes = True
material.node_tree.nodes.clear()
shader = material.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled')
shader.parametrization = 'MELANIN'
for name, value in {'Melanin': .99, 'Melanin Redness': .15, 'Roughness': .58,
                    'Radial Roughness': .52, 'Random Color': .05, 'Random Roughness': .10}.items():
    if name in shader.inputs:
        shader.inputs[name].default_value = value
output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
material.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
group = bpy.data.node_groups.new('V764_UV_FACIAL_HAIR_ATTACHMENT', 'GeometryNodeTree')
group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
inp = group.nodes.new('NodeGroupInput')
deform = group.nodes.new('GeometryNodeDeformCurvesOnSurface')
out = group.nodes.new('NodeGroupOutput')
group.links.new(inp.outputs['Geometry'], deform.inputs['Curves'])
group.links.new(deform.outputs['Curves'], out.inputs['Geometry'])
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
    obj['adaptation'] = 'Donor strand shape retained; roots fitted to native UV surface; cropped and recolored'
    obj.hide_set(True)
    obj.hide_render = True
    installed.append(obj.name)
    report['grooms'][name] = {'strands': len(paths), 'points': len(all_points),
                              'bounds': [all_points.min(0).tolist(), all_points.max(0).tolist()],
                              'surface': head.name, 'radius_m': radius, 'attribution': attribution}
    print('FITTED_HAIR', name, len(paths), flush=True)


data = donor('bystedt_curls')
donor_tree = donor_surface('bystedt_scalp')
paths, uvs = [], []
scalp_rejected = 0
restore = runpy.run_path(str(ROOT / 'native_cranium_mapping.py'))['restore_upper_head']
for first, last in zip(data['offsets'][:-1], data['offsets'][1:]):
    source = data['points'][first:last].astype(np.float64)
    root = source[0]
    # Match the two heads' scalp proportions, then bind to the actual native mesh.
    guess = (root - np.array((10., -.60, 15.30))) * np.array((.105, .11, .080)) + np.array((0., -.015, 1.665))
    attached = scalp.attach(guess)
    if attached is None:
        scalp_rejected += 1
        continue
    p, normal, uv = attached
    front = 1.703-.060*smooth((abs(p[0])-.052)/.041)
    transition = smooth((p[1]+.050)/.080)
    hairline = float(restore(front*(1-transition)+1.595*transition))
    part_x = .041+.13*(p[1]+.065)
    in_part = p[2] > 1.690 and -.09 < p[1] < .05 and abs(p[0]-part_x) < .0012
    if p[2] < hairline or in_part:
        scalp_rejected += 1
        continue
    _, donor_normal, _, _ = donor_tree.find_nearest(Vector(root))
    if donor_normal is None:
        continue
    normal_mapped = unit(np.asarray(donor_normal) / np.array((.105, .11, .080)))
    rotate = rotation(normal_mapped, normal)
    delta = (source-root) * .065
    top = float(smooth((p[2]-1.685)/.055))
    delta = delta @ rotate.T
    path = trim(p + delta, .020 + .045*top)
    # Keep imported roots and strand bodies on the visible side of the scalp.
    # The surface lookup also accounts for the donor and target having different heads.
    for index, point in enumerate(path):
        hit, n, _, distance = scalp.tree.find_nearest(Vector(point))
        if hit is not None:
            clearance = (Vector(point)-hit).dot(n)
            if clearance < .00012:
                path[index] += np.asarray(n)*(.00012-clearance)
    paths.append(path)
    uvs.append(uv)
install('V764_ASSET_SCALP', paths, uvs, .000045,
        'Daniel Bystedt - Hair Styles - CC BY-SA; adapted curly groom')
report['scalp_rejected_outside_reference_hairline'] = scalp_rejected


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
                guess[0] *= .94
                guess[2] = 1.674 + (root[2]-1.687)*.70
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
    install('V764_ASSET_' + kind, paths, uvs, radius,
            'Einar Rig (CC-BY 4.0) Blender Foundation | studio.blender.org; adapted ' + kind.lower())
    report['grooms']['V764_ASSET_' + kind]['rejected'] = rejected


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
notice = bpy.data.texts.new('V764_LICENSED_HAIR_SOURCES')
notice.write((ROOT.parent / 'licenses/hair-asset-sources.md').read_text())
assert {k.name: float(k.value) for k in mesh.shape_keys.key_blocks} == original_keys
bpy.context.view_layer.update()
report['installed_objects'] = installed
(OUT / 'v764_hair_fit.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V764_licensed_hair_trial.blend').resolve()), compress=True)

camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': installed, 'EXCLUDE_OBJECTS': old_names,
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 32, 'ADAPTIVE_THRESHOLD': .06, 'DENOISE': True}
runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
    **base, 'TAG': 'v764_asset_hair', 'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera})
runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
    **base, 'TAG': 'v764_asset_hair_front', 'VIEWS': ['front']})
runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
    **base, 'TAG': 'v764_asset_hair_motion', 'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera,
    'HEAD_TURN_DEGREES': 12., 'POSE': {'Blink.L': .65, 'Blink.R': .65}})
print('ASSET_HAIR_TRIAL_COMPLETE', installed, flush=True)
