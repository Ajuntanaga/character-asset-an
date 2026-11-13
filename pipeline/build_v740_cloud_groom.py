"""Reconstruct the native groom from the isolated V739 checkpoint on a cloud runner."""
import bpy
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
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

# Replace only unobserved scalp/rear-neck texture regions, leaving front skin.
skin = bpy.data.materials['V736_NATIVE_PHOTO_SKIN'].copy()
skin.name = 'V740_CLEAN_SCALP_NAPE'
nodes, links = skin.node_tree.nodes, skin.node_tree.links
shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
for link in list(shader.inputs['Base Color'].links):
    links.remove(link)
tex = nodes.new('ShaderNodeTexCoord')
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 25
noise.inputs['Detail'].default_value = 2
links.new(tex.outputs['Object'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (.22, .10, .047, 1)
ramp.color_ramp.elements[1].color = (.30, .148, .078, 1)
links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
head.data.materials.append(skin)
clean_slot = len(head.data.materials)-1
assigned = {'scalp': 0, 'rear_neck': 0}
for polygon, original in zip(head.data.polygons, kept):
    region = 'scalp' if original in scalp_faces else 'rear_neck' if original in neck_faces and co[list(polygon.vertices), 1].mean() > 0 else None
    if region:
        polygon.material_index = clean_slot
        assigned[region] += 1

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

def in_part(p):
    return p[2] > 1.687 and -.080 < p[1] < .050 and abs(p[0]-(.041+.13*(p[1]+.065))) < .0016

def allowed(p):
    front = 1.703-.060*smooth((abs(p[0])-.052)/.041)
    transition = smooth((p[1]+.050)/.080)
    limit = front*(1-transition)+1.595*transition
    return p[2] > limit and not in_part(p)

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
for name, value in {'Melanin': .985, 'Roughness': .38, 'Radial Roughness': .35,
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
for p, n, root_uv in guides:
    top = float(smooth((p[2]-1.678)/.050))
    # The front fringe curls outward and forward; sides sweep back from the part.
    forward = -.48 if p[1] < -.040 and p[2] > 1.687 else .75
    flow = np.array([-.32*np.sign(p[0]-.039)*top, forward, -.58*(1-top)])
    tangent = unit(flow-n*np.dot(flow, n))
    axis = unit(tangent*(.80-.16*top)+n*(.42+.27*top))
    u = unit(n-axis*np.dot(n, axis))
    v = unit(np.cross(axis, u))
    root_u, root_v = tangent, unit(np.cross(n, tangent))
    radius = rng.uniform(.0033, .0048)+top*.0013
    length = rng.uniform(.012, .021)+top*.007
    turns = rng.uniform(1.05, 1.85)
    phase = rng.uniform(-math.pi, math.pi)
    theta = phase+math.tau*turns*t
    helix = radius*emerge[:, None]*(np.cos(theta)[:, None]*u+np.sin(theta)[:, None]*v)
    guide = p+n*(.00016+(radius+.0006)*emerge[:, None])+axis*length*t[:, None]+helix
    for j in range(1, len(t)):
        hit, normal, _, _ = scalp.find_nearest(Vector(guide[j]))
        if hit is not None:
            signed = (Vector(guide[j])-hit).dot(normal)
            if signed < .0006:
                shift = .0006-signed
                guide[j] += np.array(normal)*shift
                corrections += 1
                max_correction = max(max_correction, shift)
    for _ in range(64):
        angle, radial = rng.random()*math.tau, math.sqrt(rng.random())
        root_offset = radial*.0017*(math.cos(angle)*root_u+math.sin(angle)*root_v)
        hit = attachment(p+root_offset)
        if hit is None or not allowed(hit[0]):
            continue
        q, normal, child_uv = hit
        q += normal*.00016
        packed = radial*rng.uniform(.0007, .00125)*(math.cos(angle)*u+math.sin(angle)*v)
        path = guide+(q-guide[0])[None, :]*(1-bundle[:, None])+packed*bundle[:, None]
        path += u*rng.uniform(-.00018, .00018)*np.sin(math.pi*t)[:, None]
        width = rng.uniform(.000030, .000043)
        taper = np.maximum(.04, (1-t)/.15)*np.minimum(1., 1-.08*t)
        taper[t < .85] = 1-.08*t[t < .85]
        strands.append(path)
        radii.append(width*taper)
        uvs.append(child_uv)
curl = install('V740_NATIVE_CURLS', strands, radii, uvs)
curl_count = len(strands)
del strands, radii, uvs

strands, radii, uvs = [], [], []
t = np.linspace(0, 1, 10)
for _ in range(75000):
    if len(strands) == 28000:
        break
    p, n, root_uv = sample()
    if not allowed(p):
        continue
    tangent = unit(np.cross(n, [1, .3, .1]))
    across = unit(np.cross(n, tangent))
    angle = rng.uniform(-math.pi, math.pi)
    direction = tangent*math.cos(angle)+across*math.sin(angle)
    length = rng.uniform(.003, .006)
    path = p+n*(.00015+.0018*np.sin(math.pi*t/2))[:, None]+direction*length*t[:, None]
    strands.append(path)
    radii.append(rng.uniform(.000025, .000038)*np.maximum(.06, 1-t*t))
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
