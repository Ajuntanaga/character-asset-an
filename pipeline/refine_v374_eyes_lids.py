"""Fit the downloaded BlenderKit eye and smooth the existing deformable lids.

Run once on V373 in the live GUI. Keep the previous eyes for rollback, preserve
CloudRig and body shape-key drivers, and use the current eyelid topology.
"""
from collections import defaultdict, deque
from pathlib import Path
import json
import math

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v374_natural_eyes'
OUT.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
head = rig.pose.bones['Head']
assert len(rig.animation_data.drivers) == 1957
assert not bpy.data.objects.get('V374_EYE.L'), 'Already applied; use the saved checkpoint'
if not bpy.data.objects.get('V374_SOURCE_EYEBALL'):
    with bpy.data.libraries.load(str(ROOT/'third_party/blenderkit_free/procedural_eye.blend'), link=False) as (_, loaded):
        loaded.objects = ['Eyeball', 'Cornea']
    for obj in loaded.objects:
        obj.name = 'V374_SOURCE_'+obj.name.split('.')[0].upper()
        obj.hide_render = obj.hide_viewport = True
source = bpy.data.objects['V374_SOURCE_EYEBALL']
cornea_source = bpy.data.objects['V374_SOURCE_CORNEA']

material = source.data.materials[0].copy()
material.name = 'V374_PROCEDURAL_BROWN_EYE'
group = next(n for n in material.node_tree.nodes if n.type == 'GROUP')
group.node_tree = group.node_tree.copy()
colors = {
    'Iris Primary': (.032, .012, .003, 1),
    'Iris Secondary': (.10, .044, .012, 1),
    'Iris Tertiary': (.055, .022, .006, 1),
    'Iris Dark Gaps': (.006, .002, .0007, 1),
    'Splotches': (.12, .049, .011, 1),
    'Limbus Primary': (.012, .005, .002, 1),
    'Limbus Secondary': (.004, .0017, .0007, 1),
    'Scelera': (.40, .345, .30, 1),
    'Blood Vessels/SSS': (.16, .010, .007, 1),
}
for name, value in colors.items():
    group.inputs[name].default_value = value
for name, value in {'Blood Vessels':.30, 'Blood Vessels Coverage':.48,
                    'Blood Vessels Bump':.025, 'Subsurface Scattering':.08}.items():
    group.inputs[name].default_value = value
for node in group.node_tree.nodes:
    if node.type == 'BSDF_PRINCIPLED':
        weight = next((s for s in node.inputs if s.name == 'Weight'), None)
        if weight is not None and not weight.is_linked:
            weight.default_value = 1.
        node.inputs['Subsurface Scale'].default_value = .0007

# A thin wet surface makes the iris visible without the source asset's
# lamp-specific caustic effect. The original corneal geometry is retained.
cornea_material = bpy.data.materials['V362_CORNEA_PHYSICAL'].copy()
cornea_material.name = 'V374_CORNEAL_TEAR_FILM'
for node in cornea_material.node_tree.nodes:
    if node.type == 'BSDF_GLOSSY':
        node.inputs['Roughness'].default_value = .035

def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)

new_eyes = {}
for side in ('L', 'R'):
    previous = bpy.data.objects['V362_EYE.'+side]
    eye = source.copy()
    eye.data = source.data.copy()
    eye.name = 'V374_EYE.'+side
    scene.collection.objects.link(eye)
    eye.parent = bpy.data.objects['V362_GAZE.'+side]
    eye.matrix_parent_inverse = Matrix.Identity(4)
    eye.matrix_basis = previous.matrix_basis.copy()
    eye.hide_render = eye.hide_viewport = False
    eye.hide_set(False)
    eye.data.materials.clear()
    eye.data.materials.append(material)
    for key in eye.data.shape_keys.key_blocks:
        for vertex in key.data:
            x, y, z = vertex.co
            r = math.hypot(x, y)
            if z > .005:
                factor = .68+.32*smooth((r-.0072)/.0038)
                vertex.co.x = x*factor
                vertex.co.y = y*factor
        if key.name != 'Pupil':
            key.value = .35 if key.name == 'Dilation' else 0.
    for mod in eye.modifiers:
        if mod.type == 'SUBSURF':
            mod.levels = mod.render_levels = 2
    eye['asset_source'] = 'BlenderKit / Joshua Jennings / Realistic Rigged Procedural Eye'
    eye['license'] = 'royalty_free; metadata in third_party/blenderkit_free'
    cornea = cornea_source.copy()
    cornea.data = cornea_source.data.copy()
    cornea.name = 'V374_CORNEA.'+side
    scene.collection.objects.link(cornea)
    cornea.parent = eye
    cornea.matrix_parent_inverse = Matrix.Identity(4)
    cornea.matrix_basis = Matrix.Identity(4)
    for vertex in cornea.data.vertices:
        p = cornea_source.matrix_basis @ vertex.co
        vertex.co = (p.x*.68, p.y*.68, .0102+(p.z-.0102)*.45+.0006)
    cornea.data.materials.clear()
    cornea.data.materials.append(cornea_material)
    cornea.hide_render = cornea.hide_viewport = False
    cornea.hide_set(False)
    for mod in cornea.modifiers:
        if mod.type == 'SUBSURF':
            mod.levels = mod.render_levels = 2
    previous.hide_render = True
    previous.hide_set(True)
    new_eyes[side] = (eye, cornea)
bpy.context.view_layer.update()

# Find the existing regular lid rows from topology, not historical indices.
mesh = body.data
keys = mesh.shape_keys.key_blocks
basis = keys['Basis']
material_id = list(mesh.materials).index(bpy.data.materials['V365_LID_SKIN'])
edge_counts = defaultdict(int)
for poly in mesh.polygons:
    for edge in poly.edge_keys:
        edge_counts[tuple(sorted(edge))] += 1
report = {'eyes': {}, 'asset': material.name}
for side in ('L', 'R'):
    sign = 1 if side == 'L' else -1
    polygons = [p for p in mesh.polygons if p.material_index == material_id
                and basis.data[p.vertices[0]].co.x*sign > 0]
    adjacent = defaultdict(set)
    for poly in polygons:
        for a, b in poly.edge_keys:
            adjacent[a].add(b)
            adjacent[b].add(a)
    inner = {v for v, neighbors in adjacent.items()
             if any(edge_counts[tuple(sorted((v, n)))] == 1 for n in neighbors)}
    assert len(inner) == 64, (side, len(inner))
    distance = {v: 0 for v in inner}
    queue = deque(inner)
    while queue:
        v = queue.popleft()
        for n in adjacent[v]:
            if n not in distance:
                distance[n] = distance[v]+1
                queue.append(n)
    assert max(distance.values()) == 11
    left = min(inner, key=lambda v: basis.data[v].co.x)
    right = max(inner, key=lambda v: basis.data[v].co.x)
    xmin, xmax = basis.data[left].co.x, basis.data[right].co.x
    zleft, zright = basis.data[left].co.z, basis.data[right].co.z
    blink = keys['Blink.'+side]
    edges = []
    max_change = 0.
    for start in inner:
        old = basis.data[start].co.copy()
        u = (old.x-xmin)/(xmax-xmin)
        baseline = zleft*(1-u)+zright*u
        upper = old.z >= baseline
        new_z = baseline + (.0068*math.sin(math.pi*u)**.75 if upper
                            else -.0036*math.sin(math.pi*u)**.85)
        change = new_z-old.z
        v = start
        for row in range(11):
            weight = (1-row/11)**1.5
            delta = Vector((0, 0, change*weight))
            for key in keys:
                if key.name != 'Blink.'+side:
                    key.data[v].co += delta
            max_change = max(max_change, delta.length)
            next_row = [n for n in adjacent[v] if distance[n] == row+1]
            assert len(next_row) == 1, (side, v, row, next_row)
            v = next_row[0]
        edges.append(start)
    # Project just the lids outside the fitted eye/cornea, including full blink.
    # The skin's outer join remains fixed.
    dg = bpy.context.evaluated_depsgraph_get()
    verts, faces = [], []
    for obj in new_eyes[side]:
        evaluated = obj.evaluated_get(dg)
        evaluated_mesh = evaluated.to_mesh()
        offset = len(verts)
        verts.extend(body.matrix_world.inverted() @ evaluated.matrix_world @ v.co for v in evaluated_mesh.vertices)
        faces.extend([offset+i for i in p.vertices] for p in evaluated_mesh.polygons)
        evaluated.to_mesh_clear()
    surface = BVHTree.FromPolygons(verts, faces, all_triangles=False)
    pushed = 0
    for v, row in distance.items():
        if row == 11:
            continue
        for key in keys:
            p = key.data[v].co
            hit, _, _, _ = surface.ray_cast(Vector((p.x, -.25, p.z)), Vector((0, 1, 0)), .4)
            if hit is not None and p.y > hit.y-.00055:
                p.y = hit.y-.00055
                pushed += 1
    # Refit the independent wet/lash margin to the same open and closed edges.
    margin = bpy.data.objects['V369_LID_MARGIN.'+side]
    mk = margin.data.shape_keys.key_blocks
    old_centers = []
    for i in range(64):
        old_centers.append(sum((mk['Basis'].data[i*6+k].co for k in range(6)), Vector())/6)
    order = [min(inner, key=lambda v: (keys['Blink.'+side].data[v].co.x-p.x)**2
                 +(keys['Blink.'+side].data[v].co.z-p.z)**2
                 +(basis.data[v].co.z-p.z)**2) for p in old_centers]
    # Original angular order gives a unique matching even at the corners.
    order = sorted(inner, key=lambda v: math.atan2(
        (1 if basis.data[v].co.z >= zleft+(zright-zleft)*(basis.data[v].co.x-xmin)/(xmax-xmin) else -1)
        * math.sqrt(max(0, 1-((2*basis.data[v].co.x-xmin-xmax)/(xmax-xmin))**2)),
        -(2*basis.data[v].co.x-xmin-xmax)/(xmax-xmin)) % math.tau)
    for key_name, body_key in [('Basis', basis), ('Blink', blink)]:
        edge = [body_key.data[v].co.copy() for v in order]
        for i, p in enumerate(edge):
            top = i <= 32
            r = .00014 if top else .00023
            tangent = (edge[(i+1)%64]-edge[i-1]).normalized()
            front = Vector((0, -1, 0))
            across = tangent.cross(front).normalized()
            for k in range(6):
                a = k*math.tau/6
                mk[key_name].data[i*6+k].co = p+front*.00007+r*(math.cos(a)*front+math.sin(a)*across)
    margin.data.update()
    report['eyes'][side] = {'lid_vertices':len(distance), 'inner_vertices':len(inner),
                            'max_contour_change_mm':max_change*1000, 'eye_clearance_projections':pushed}
mesh.update()
# Gloss remains on the wet margin; the upper margin stays dark brown.
wet = bpy.data.materials['V367_WATERLINE'].node_tree.nodes
for node in wet:
    if node.type == 'BSDF_PRINCIPLED':
        node.inputs['Base Color'].default_value = (.19, .070, .043, 1)
        node.inputs['Roughness'].default_value = .18
        node.inputs['Coat Weight'].default_value = .32
rig.update_tag()
bpy.context.view_layer.update()
report['rig_drivers'] = len(rig.animation_data.drivers)
report['body_keys'] = list(keys.keys())
(OUT/'eye_report.json').write_text(json.dumps(report, indent=2))
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = 800
scene.render.resolution_y = 450
scene.camera.data.ortho_scale = .17
scene.camera.location = (0, -1.4, 1.65)
scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_natural_eyes_v374.blend'), compress=True)
for name, value in [('open', 0.), ('closed', 1.)]:
    head['Blink.L'] = head['Blink.R'] = value
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(OUT/f'v374_eyes_{name}.png')
    bpy.ops.render.render(write_still=True)
head['Blink.L'] = head['Blink.R'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
print(json.dumps(report))
