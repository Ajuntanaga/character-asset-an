"""Replace the pinched lid surface with a shallow, globe-following fold."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

root = Path(__file__).resolve().parents[1]
out = root / 'production_v365_face_surface'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert len(rig.animation_data.drivers) == 1957
landmarks = json.loads((root / 'production_v362_face_anatomy/actual_face_landmarks.json').read_text())['landmarks']
specs = json.loads((root / 'production_v362_face_anatomy/eyes_lids_build.json').read_text())['eyes']
source = bpy.data.meshes['V362_BODY_BEFORE_EYE_SOCKETS']
coords = [body.matrix_world @ v.co for v in source.vertices]
bvh = BVHTree.FromPolygons(coords, [list(p.vertices) for p in source.polygons])


def preserve(obj):
    name = 'V365_BEFORE_' + obj.name
    if name not in bpy.data.meshes:
        backup = obj.data.copy()
        backup.name = name
        backup.use_fake_user = True
    return bpy.data.meshes[name]


def smooth(v):
    t = max(0., min(1., v))
    return t*t*(3-2*t)


def interpolate(points, x):
    for a, b in zip(points, points[1:]):
        if a.x <= x <= b.x:
            return a.lerp(b, (x-a.x)/(b.x-a.x))
    return (points[0] if x < points[0].x else points[-1]).copy()


def sample_uv(x, z):
    p, normal, index, distance = bvh.ray_cast(Vector((x, -.7, z)), Vector((0, 1, 0)))
    if p is None:
        raise ValueError((x, z))
    face = source.polygons[index]
    vi, li = list(face.vertices)[:3], list(face.loop_indices)[:3]
    uv = [Vector((*source.uv_layers.active.data[j].uv, 0)) for j in li]
    return barycentric_transform(p, *[coords[j] for j in vi], *uv).xy


for prop in ('Blink.L', 'Blink.R', 'JawOpen', 'GazeHorizontal', 'GazeVertical'):
    head[prop] = 0.
rig.update_tag()
bpy.context.view_layer.update()
body_before = preserve(body)
material = bpy.data.materials.get('V365_LID_SKIN')
if material is None:
    material = body.data.materials[0].copy()
    material.name = 'V365_LID_SKIN'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    original = nodes.get('Image Texture')
    uvmap = nodes.new('ShaderNodeUVMap')
    uvmap.uv_map = 'V365_CleanSkin'
    clean = nodes.new('ShaderNodeTexImage')
    clean.image = original.image
    clean.label = 'Adjacent cheek albedo for the unfolding lid'
    links.new(uvmap.outputs['UV'], clean.inputs['Vector'])
    attribute = nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = 'V365_LidAlbedoBlend'
    mix = nodes.new('ShaderNodeMixRGB')
    links.new(attribute.outputs['Fac'], mix.inputs[0])
    links.new(original.outputs['Color'], mix.inputs[1])
    links.new(clean.outputs['Color'], mix.inputs[2])
    shader = nodes.get('Principled BSDF')
    links.new(mix.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = .55
    shader.inputs['Specular IOR Level'].default_value = .25

report = {'eyes': {}, 'body_vertices': 0, 'render_engine': 'CYCLES'}
for side in ('L', 'R'):
    obj = bpy.data.objects['V362_LIDS.'+side]
    old = preserve(obj).shape_keys.key_blocks['Basis']
    basis, blink = (obj.data.shape_keys.key_blocks[n] for n in ('Basis', 'Blink'))
    center = Vector(specs[side]['center'])
    center.y -= .0045
    radius = specs[side]['radius']
    anchor = bpy.data.objects['V362_EYE_ANCHOR.'+side]
    if 'V365_before_matrix_basis' not in anchor:
        anchor['V365_before_matrix_basis'] = [v for row in anchor.matrix_basis for v in row]
    anchor.location = center
    upper = [Vector(p['world']) for p in landmarks[side]['upper']]
    lower = [Vector(p['world']) for p in landmarks[side]['lower']]
    clean_uv = obj.data.uv_layers.get('V365_CleanSkin') or obj.data.uv_layers.new(name='V365_CleanSkin')
    blend = obj.data.attributes.get('V365_LidAlbedoBlend') or obj.data.attributes.new('V365_LidAlbedoBlend', 'FLOAT', 'POINT')
    uv_values = []

    def globe_y(x, z):
        squared = radius**2-(x-center.x)**2-(z-center.z)**2
        return center.y-math.sqrt(squared) if squared > 0 else None

    for j in range(8):
        t = j/7
        for i in range(64):
            sine = math.sin(2*math.pi*i/64)
            top = sine >= 0
            edge, outer = old.data[i].co.copy(), old.data[7*64+i].co.copy()
            edge.z += (-.0007 if top else .0004)*abs(sine)
            edge.y = globe_y(edge.x, edge.z)-.0008
            point = edge.lerp(outer, t)
            point.y -= (.0016 if top else .0007)*math.sin(math.pi*t)*abs(sine)
            gy = globe_y(point.x, point.z)
            if gy is not None and j < 7:
                point.y = min(point.y, gy-.0008)
            basis.data[j*64+i].co = point
            seam = interpolate(upper, edge.x).z*.23+interpolate(lower, edge.x).z*.77
            closed_edge = Vector((edge.x, globe_y(edge.x, seam)-.0009, seam+(.000035 if top else -.000035)))
            closed = closed_edge.lerp(outer, t)
            closed.y -= (.0020 if top else .0006)*math.sin(math.pi*t)*abs(sine)
            gy = globe_y(closed.x, closed.z)
            if gy is not None and j < 7:
                closed.y = min(closed.y, gy-.0009)
            blink.data[j*64+i].co = closed
            uv_values.append(sample_uv(point.x, 1.620+.005*t))
            blend.data[j*64+i].value = .92*(1-smooth((t-.35)/.65))
    for loop in obj.data.loops:
        clean_uv.data[loop.index].uv = uv_values[loop.vertex_index]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj.data.update()

    adjusted = 0
    for index, vertex in enumerate(body_before.shape_keys.key_blocks['Basis'].data):
        p = vertex.co
        if p.y > center.y or abs(p.x-center.x) > radius or abs(p.z-center.z) > radius:
            continue
        gy = globe_y(p.x, p.z)
        if gy is not None and p.y > gy-.0008:
            delta = gy-.0008-p.y
            for key in body.data.shape_keys.key_blocks:
                key.data[index].co.y = body_before.shape_keys.key_blocks[key.name].data[index].co.y+delta
            adjusted += 1
    report['body_vertices'] += adjusted
    report['eyes'][side] = {'center': list(center), 'radius': radius, 'skin_adjustments': adjusted}

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 5
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 3
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = .40
scene.camera.location = (0, -1.4, 1.66)
scene.camera.rotation_euler = (Vector((0, 0, 1.66))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
rig.update_tag()
bpy.context.view_layer.update()
for name, closed in [('v365_neutral', 0.), ('v365_blink', 1.)]:
    head['Blink.L'] = head['Blink.R'] = closed
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
head['Blink.L'] = head['Blink.R'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
report['rig_drivers'] = len(rig.animation_data.drivers)
(out/'lid_surface_report.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_lid_surface_v365.blend'), compress=True)
print(json.dumps(report))
