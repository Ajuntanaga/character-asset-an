"""Give the lid patch a curved globe-to-orbit transition in neutral and blink."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

root = Path(__file__).resolve().parents[1]
out = root/'production_v366_lid_curvature'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert len(rig.animation_data.drivers) == 1957
landmarks = json.loads((root/'production_v362_face_anatomy/actual_face_landmarks.json').read_text())['landmarks']
specs = json.loads((root/'production_v362_face_anatomy/eyes_lids_build.json').read_text())['eyes']
source = bpy.data.meshes['V362_BODY_BEFORE_EYE_SOCKETS']
coords = [body.matrix_world@v.co for v in source.vertices]
bvh = BVHTree.FromPolygons(coords, [list(p.vertices) for p in source.polygons])


def preserve(obj):
    name = 'V366_BEFORE_'+obj.name
    if name not in bpy.data.meshes:
        backup = obj.data.copy()
        backup.name = name
        backup.use_fake_user = True
    return bpy.data.meshes[name]


def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)


def interp(points, x):
    for a, b in zip(points, points[1:]):
        if a.x <= x <= b.x:
            return a.lerp(b, (x-a.x)/(b.x-a.x))
    return (points[0] if x < points[0].x else points[-1]).copy()


def sample(x, z):
    p, normal, index, _ = bvh.ray_cast(Vector((x, -.7, z)), Vector((0, 1, 0)))
    if p is None:
        raise ValueError((x, z))
    face = source.polygons[index]
    vi, li = list(face.vertices)[:3], list(face.loop_indices)[:3]
    uv = [Vector((*source.uv_layers.active.data[j].uv, 0)) for j in li]
    return p, normal, barycentric_transform(p, *[coords[j] for j in vi], *uv).xy


for prop in ('Blink.L', 'Blink.R', 'JawOpen', 'GazeHorizontal', 'GazeVertical'):
    head[prop] = 0.
rig.update_tag()
bpy.context.view_layer.update()
body_before = preserve(body)
report = {'eyes': {}}
for side in ('L', 'R'):
    obj = bpy.data.objects['V362_LIDS.'+side]
    preserve(obj)
    center = Vector(specs[side]['center'])
    center.y -= .0105 if side == 'L' else .009
    radius = specs[side]['radius']
    anchor = bpy.data.objects['V362_EYE_ANCHOR.'+side]
    anchor.location = center
    upper = [Vector(p['world']) for p in landmarks[side]['upper']]
    lower = [Vector(p['world']) for p in landmarks[side]['lower']]
    xmin, xmax = upper[0].x, upper[-1].x
    midx, half = (xmin+xmax)/2, (xmax-xmin)/2
    midz = sum(p.z for p in upper+lower)/14
    basis, blink = (obj.data.shape_keys.key_blocks[n] for n in ('Basis', 'Blink'))
    original_uv = obj.data.uv_layers[0]
    clean_uv = obj.data.uv_layers['V365_CleanSkin']
    blend = obj.data.attributes['V365_LidAlbedoBlend']
    texture_uvs, cheek_uvs = [], []

    def globe_y(x, z):
        squared = radius**2-(x-center.x)**2-(z-center.z)**2
        return center.y-math.sqrt(squared) if squared > 0 else None

    for j in range(8):
        t = j/7
        for i in range(64):
            theta = 2*math.pi*i/64
            sine, cosine = math.sin(theta), math.cos(theta)
            top = sine >= 0
            x = midx-half*cosine
            edge = interp(upper if top else lower, x)
            edge.z += (-.0012 if top else .0006)*abs(sine)
            seam = interp(upper, x).z*.23+interp(lower, x).z*.77
            ox = midx-half*1.52*cosine
            oz = midz+(.0205 if top else .0165)*sine
            outer, normal, _ = sample(ox, oz)
            outer.y -= .00015
            for key, ez in ((basis, edge.z), (blink, seam+(.000035 if top else -.000035))):
                inner = Vector((x, globe_y(x, ez)-.00085, ez))
                p = inner.lerp(outer, t)
                dx, dz = outer.x-inner.x, outer.z-inner.z
                denom = max(.002, center.y-globe_y(inner.x, inner.z))
                slope0 = ((inner.x-center.x)*dx+(inner.z-center.z)*dz)/denom
                slope1 = -(normal.x*dx+normal.z*dz)/normal.y if abs(normal.y) > .1 else 0.
                slope0 = max(-.020, min(.020, slope0))
                slope1 = max(-.020, min(.020, slope1))
                p.y = ((2*t**3-3*t*t+1)*inner.y+(t**3-2*t*t+t)*slope0
                       +(-2*t**3+3*t*t)*outer.y+(t**3-t*t)*slope1)
                gy = globe_y(p.x, p.z)
                if gy is not None and j < 7:
                    limit = gy-.00085
                    # A smooth minimum avoids a ridge at the collision envelope.
                    p.y = .5*(p.y+limit-math.sqrt((p.y-limit)**2+.00035**2))
                key.data[j*64+i].co = p
            p = basis.data[j*64+i].co
            texture_uvs.append(sample(p.x, p.z)[2])
            cheek_uvs.append(sample(p.x, 1.620+.005*t)[2])
            blend.data[j*64+i].value = 1-smooth((t-.48)/.48)
    for loop in obj.data.loops:
        original_uv.data[loop.index].uv = texture_uvs[loop.vertex_index]
        clean_uv.data[loop.index].uv = cheek_uvs[loop.vertex_index]
    obj.data.update()
    adjusted = 0
    for index, vertex in enumerate(body_before.shape_keys.key_blocks['Basis'].data):
        p = vertex.co
        if p.y > center.y or abs(p.x-center.x) > radius or abs(p.z-center.z) > radius:
            continue
        gy = globe_y(p.x, p.z)
        if gy is not None and p.y > gy-.00085:
            delta = gy-.00085-p.y
            for key in body.data.shape_keys.key_blocks:
                key.data[index].co.y = body_before.shape_keys.key_blocks[key.name].data[index].co.y+delta
            adjusted += 1
    report['eyes'][side] = {'center': list(center), 'radius': radius, 'body_vertices_adjusted': adjusted}

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = scene.render.resolution_y = 700
scene.camera.data.ortho_scale = .40
scene.camera.location = (0, -1.4, 1.66)
scene.camera.rotation_euler = (Vector((0, 0, 1.66))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
for name, closed in [('v366_neutral', 0.), ('v366_blink', 1.)]:
    head['Blink.L'] = head['Blink.R'] = closed
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
head['Blink.L'] = head['Blink.R'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
report['rig_drivers'] = len(rig.animation_data.drivers)
(out/'lid_curvature_report.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_lid_curvature_v366.blend'), compress=True)
print(json.dumps(report))
