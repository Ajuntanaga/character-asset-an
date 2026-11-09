"""Fit CC0 dental anatomy and a continuous lip/cavity opening to the actual face."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v363_mouth'
OUT.mkdir(exist_ok=True)
FACE = ROOT / 'production_v362_face_anatomy'
scene = bpy.context.scene
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
assert len(rig.animation_data.drivers) == 1957
assert body.data.shape_keys is None, 'Build this checkpoint from V362, not an already cut mouth.'
source = bpy.data.meshes['V362_BODY_BEFORE_EYE_SOCKETS']
before = body.data.copy()
before.name = 'V363_BODY_BEFORE_MOUTH'
before.use_fake_user = True
coords = [body.matrix_world @ v.co for v in source.vertices]
bvh = BVHTree.FromPolygons(coords, [list(p.vertices) for p in source.polygons])
landmarks = json.loads((FACE / 'actual_face_landmarks.json').read_text())['landmarks']
collection = bpy.data.collections.new('V363_MOUTH_ANATOMY')
scene.collection.children.link(collection)


def surface(x, z):
    p, n, index, distance = bvh.ray_cast(Vector((x, -.7, z)), Vector((0, 1, 0)))
    if p is None:
        raise RuntimeError(f'Missing face at {x}, {z}')
    face = source.polygons[index]
    vi, li = list(face.vertices)[:3], list(face.loop_indices)[:3]
    uv = [Vector((*source.uv_layers.active.data[j].uv, 0)) for j in li]
    return p, barycentric_transform(p, *[coords[j] for j in vi], *uv).xy


def interp(points, x):
    for a, b in zip(points, points[1:]):
        if a.x <= x <= b.x:
            return a.lerp(b, (x-a.x)/(b.x-a.x))
    return points[0].copy() if x < points[0].x else points[-1].copy()


def smooth(value):
    t = max(0., min(1., value))
    return t*t*(3-2*t)


def drive(owner, path, expression='v', index=None):
    curve = owner.driver_add(path) if index is None else owner.driver_add(path, index)
    driver = curve.driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name = 'v'
    var.type = 'SINGLE_PROP'
    var.targets[0].id = rig
    var.targets[0].data_path = 'pose.bones["Head"]["JawOpen"]'
    driver.expression = expression


def head_parent(obj, world):
    bone = rig.pose.bones['DEF-Head']
    frame = rig.matrix_world @ bone.matrix @ Matrix.Translation((0, bone.bone.length, 0))
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = bone.name
    obj.matrix_parent_inverse = frame.inverted()
    obj.matrix_basis = world


def material(name, color, roughness, subsurface=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Subsurface Weight'].default_value = subsurface
    shader.inputs['Subsurface Scale'].default_value = .001
    shader.inputs['Coat Weight'].default_value = .15
    shader.inputs['Coat Roughness'].default_value = .18
    return mat


def make_mesh(name, vertices, faces, materials, uv_coords=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if uv_coords:
        layer = mesh.uv_layers.new(name=source.uv_layers.active.name)
        for loop in mesh.loops:
            layer.data[loop.index].uv = uv_coords[loop.vertex_index]
    return obj


def add_shape(obj, points):
    obj.shape_key_add(name='Basis')
    key = obj.shape_key_add(name='JawOpen')
    for vertex, point in zip(key.data, points):
        vertex.co = point
    drive(key, 'value')


# Inner eyelid UVs must sample skin, not the painted sclera on the source mesh.
for side in ('L', 'R'):
    lids = bpy.data.objects['V362_LIDS.'+side]
    upper = [Vector(p['world']) for p in landmarks[side]['upper']]
    lower = [Vector(p['world']) for p in landmarks[side]['lower']]
    xmin, xmax = upper[0].x, upper[-1].x
    midx = (xmin+xmax)/2
    midz = sum(p.z for p in upper+lower)/14
    uvs = []
    for j in range(8):
        t = .42 + .58*j/7
        for i in range(64):
            theta = 2*math.pi*i/64
            x = midx-(xmax-xmin)/2*math.cos(theta)
            edge = interp(upper if math.sin(theta) >= 0 else lower, x)
            ox, oz = midx+(x-midx)*1.45, midz+(edge.z-midz)*2.65
            _, uv = surface(x+(ox-x)*t, edge.z+(oz-edge.z)*t)
            uvs.append(uv)
    for loop in lids.data.loops:
        lids.data.uv_layers.active.data[loop.index].uv = uvs[loop.vertex_index]

upper = [Vector(p['world']) for p in landmarks['mouth']['upper']]
lower = [Vector(p['world']) for p in landmarks['mouth']['lower']]
xmin, xmax = upper[0].x, upper[-1].x
midx = (xmin+xmax)/2
midz = 1.572
pivot = Vector((0, -.002, 1.616))
angle = math.radians(18)
rotation = Matrix.Rotation(angle, 3, 'X')


def jaw_rotate(p):
    return pivot + rotation @ (p-pivot)


def jaw_weight(p):
    seam = (interp(upper, p.x).z + interp(lower, p.x).z)/2
    lower_face = 1-smooth((p.z-(seam-.014))/.029)
    front = 1-smooth((p.y+.014)/.055)
    neck = smooth((p.z-1.480)/.038)
    return lower_face*front*neck


count, rows = 96, 10
vertices, opened, uvs, outer, aperture, inner_weights = [], [], [], [], [], []
for j in range(rows):
    t = j/(rows-1)
    for i in range(count):
        theta = 2*math.pi*i/count
        sine = math.sin(theta)
        x = midx-(xmax-xmin)/2*math.cos(theta)
        top = sine >= 0
        edge = interp(upper if top else lower, x)
        seam = (interp(upper, x).z+interp(lower, x).z)/2
        iz = seam + .00018*sine
        ox = midx+(x-midx)*1.40
        oz = midz+.017*sine
        px, pz = x+(ox-x)*t, iz+(oz-iz)*t
        point, _ = surface(px, pz)
        point.y -= .0004
        # Keep the original lip/skin coloration while narrowing the neutral slit.
        _, uv = surface(px, edge.z+(oz-edge.z)*t)
        vertices.append(tuple(point))
        uvs.append(tuple(uv))
        inner_weight = .5*(1-math.tanh(6*sine)/math.tanh(6))
        weight = inner_weight*(1-t)**2 + jaw_weight(point)*(1-(1-t)**2)
        target = point.lerp(jaw_rotate(point), weight)
        target.z += .002*max(0., sine)*(1-t)**2
        opened.append(tuple(target))
        if j == 0:
            aperture.append(point.copy())
            inner_weights.append(inner_weight)
        if j == rows-1:
            outer.append((px, pz))
faces = [(j*count+i, j*count+(i+1)%count, (j+1)*count+(i+1)%count, (j+1)*count+i)
         for j in range(rows-1) for i in range(count)]
lips = make_mesh('V363_LIPS', vertices, faces, [body.data.materials[0]], uvs)
head_parent(lips, Matrix.Identity(4))
add_shape(lips, opened)
sub = lips.modifiers.new('Lip loops', 'SUBSURF')
sub.levels = 1
sub.render_levels = 2

# The replacement patch overlaps the retained original by 1.5-4 mm.
bm = bmesh.new()
bm.from_mesh(body.data)
remove = []
for face in bm.faces:
    p = face.calc_center_median()
    if p.y < -.060 and ((p.x-midx)/((xmax-xmin)*.70*.91))**2 + ((p.z-midz)/(.017*.91))**2 < 1:
        remove.append(face)
bmesh.ops.delete(bm, geom=remove, context='FACES')
bm.to_mesh(body.data)
bm.free()
body.data.update()
body_open = []
for vertex in body.data.vertices:
    p = vertex.co.copy()
    body_open.append(p.lerp(jaw_rotate(p), jaw_weight(p)))
add_shape(body, body_open)

teeth = material('V363_ENAMEL', (.58, .49, .36), .28, .12)
gums = material('V363_GUMS', (.19, .035, .030), .38, .16)
tongue_mat = material('V363_TONGUE', (.25, .057, .050), .43, .18)
cavity_mat = material('V363_ORAL_MUCOSA', (.028, .004, .003), .48, .04)

jaw = bpy.data.objects.new('V363_JAW_PIVOT', None)
collection.objects.link(jaw)
jaw.empty_display_size = .008
head_parent(jaw, Matrix.Translation(pivot))
jaw.rotation_mode = 'XYZ'
drive(jaw, 'rotation_euler', f'v*{angle}', 0)
head['JawOpen'] = 0.0
head.id_properties_ui('JawOpen').update(min=0., max=1., description='18 degree fitted jaw opening')

dental_source = bpy.data.objects['V362_SOURCE_Jaw'].data
components = json.loads((FACE/'jaw_components.json').read_text())['components']
groups = {'UPPER': [], 'LOWER': [], 'TONGUE': []}
material_for_index = {}
for component in components:
    name = 'TONGUE' if component['count'] == 310 else ('UPPER' if component['center'][2] > .038 else 'LOWER')
    groups[name].extend(component['indices'])
    material_index = 2 if name == 'TONGUE' else (1 if component['count'] == 986 else 0)
    for index in component['indices']:
        material_for_index[index] = material_index
for name, indices in groups.items():
    index_map = {old: new for new, old in enumerate(indices)}
    transformed = [Vector((dental_source.vertices[i].co.x*.96,
                           dental_source.vertices[i].co.y*.96-.068,
                           dental_source.vertices[i].co.z*.96+1.538)) for i in indices]
    if name != 'UPPER':
        transformed = [p-pivot for p in transformed]
    polys = [p for p in dental_source.polygons if all(i in index_map for i in p.vertices)]
    obj = make_mesh('V363_DENTAL_'+name, transformed,
                    [tuple(index_map[i] for i in p.vertices) for p in polys], [teeth, gums, tongue_mat])
    for polygon, original in zip(obj.data.polygons, polys):
        polygon.material_index = material_for_index[original.vertices[0]]
    if name == 'UPPER':
        head_parent(obj, Matrix.Identity(4))
    else:
        obj.parent = jaw
    sub = obj.modifiers.new('Dental surface', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2

cavity_vertices, cavity_opened = [], []
for j in range(5):
    for i, edge in enumerate(aperture):
        theta = 2*math.pi*i/count
        sine = math.sin(theta)
        if j == 0:
            p = edge+Vector((0, .0002, 0))
        elif j == 1:
            p = Vector((edge.x*.98, edge.y+.006, edge.z+.005*sine))
        else:
            scale, depth, height = {2: (.92, -.060, .021), 3: (.75, -.025, .023), 4: (.38, -.003, .014)}[j]
            p = Vector((midx+(edge.x-midx)*scale, depth, midz+height*sine))
        cavity_vertices.append(tuple(p))
        target = p.lerp(jaw_rotate(p), inner_weights[i])
        target.z += .002*max(0., sine)*(1-j/4)
        cavity_opened.append(tuple(target))
cavity_faces = [tuple(reversed((j*count+i, j*count+(i+1)%count, (j+1)*count+(i+1)%count, (j+1)*count+i)))
                for j in range(4) for i in range(count)]
cavity_faces.append(tuple(reversed(range(4*count, 5*count))))
cavity = make_mesh('V363_MOUTH_CAVITY', cavity_vertices, cavity_faces, [cavity_mat])
head_parent(cavity, Matrix.Identity(4))
add_shape(cavity, cavity_opened)
sub = cavity.modifiers.new('Mucosa continuity', 'SUBSURF')
sub.levels = 1
sub.render_levels = 2

scene.render.engine = 'BLENDER_EEVEE'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
camera = scene.camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .40


def render(name, amount=0., blink=0., three_quarter=False):
    head['JawOpen'] = amount
    head['Blink.L'] = head['Blink.R'] = blink
    camera.location = (.65, -1.25, 1.65) if three_quarter else (0, -1.4, 1.66)
    target = Vector((0, 0, 1.65 if three_quarter else 1.66))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(OUT / (name+'.png'))
    bpy.ops.render.render(write_still=True)


report = {'removed_original_mouth_faces': len(remove), 'lip_vertices': len(vertices),
          'dental_components': len(components), 'jaw_pivot': list(pivot), 'jaw_degrees': 18,
          'rig_driver_count': len(rig.animation_data.drivers), 'license': 'Blender Studio CC0 human base meshes v1.4.1'}
(OUT/'mouth_build.json').write_text(json.dumps(report, indent=2))
render('v363_neutral_front')
render('v363_open_front', .75)
render('v363_open_three_quarter', .75, three_quarter=True)
render('v363_blink_front', blink=1.)
head['JawOpen'] = head['Blink.L'] = head['Blink.R'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_mouth_anatomy_v363.blend'), compress=True)
print(json.dumps(report))
