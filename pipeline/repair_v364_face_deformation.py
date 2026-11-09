"""Repair lid coverage and corner-weighted jaw motion in the V363 checkpoint."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix

root = Path(__file__).resolve().parents[1]
out = root/'production_v364_face_deformation'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
head = rig.pose.bones['Head']
assert len(rig.animation_data.drivers) == 1957
landmarks = json.loads((root/'production_v362_face_anatomy/actual_face_landmarks.json').read_text())['landmarks']
eye_specs = json.loads((root/'production_v362_face_anatomy/eyes_lids_build.json').read_text())['eyes']


def interpolate(points, x):
    for a, b in zip(points, points[1:]):
        if a.x <= x <= b.x:
            return a.lerp(b, (x-a.x)/(b.x-a.x))
    return (points[0] if x < points[0].x else points[-1]).copy()


def smooth(v):
    t = max(0., min(1., v))
    return t*t*(3-2*t)


def preserve_mesh(obj):
    name = 'V364_BEFORE_'+obj.name
    if name not in bpy.data.meshes:
        backup = obj.data.copy()
        backup.name = name
        backup.use_fake_user = True
    return bpy.data.meshes[name]


for p in ('Blink.L', 'Blink.R', 'JawOpen', 'GazeHorizontal', 'GazeVertical'):
    head[p] = 0.
rig.update_tag()
bpy.context.view_layer.update()
report = {'lids': {}, 'body_coverage_vertices': 0, 'maximum_body_adjustment_mm': 0.}
body_backup = preserve_mesh(body)
body_basis = body.data.shape_keys.key_blocks['Basis']
body_old = body_backup.shape_keys.key_blocks['Basis']

for side in ('L', 'R'):
    ob = bpy.data.objects['V362_LIDS.'+side]
    backup = preserve_mesh(ob)
    old = backup.shape_keys.key_blocks['Basis']
    basis = ob.data.shape_keys.key_blocks['Basis']
    blink = ob.data.shape_keys.key_blocks['Blink']
    center = Vector(eye_specs[side]['center'])
    radius = eye_specs[side]['radius']
    upper = [Vector(p['world']) for p in landmarks[side]['upper']]
    lower = [Vector(p['world']) for p in landmarks[side]['lower']]

    def globe_y(x, z):
        squared = radius**2-(x-center.x)**2-(z-center.z)**2
        return center.y-math.sqrt(squared) if squared > 0 else None

    for i in range(64):
        theta = 2*math.pi*i/64
        sine = math.sin(theta)
        top = sine >= 0
        edge, outer = old.data[i].co.copy(), old.data[7*64+i].co.copy()
        seam = interpolate(upper, edge.x).z*.23+interpolate(lower, edge.x).z*.77
        seam_y = globe_y(edge.x, seam)-.00095
        for j in range(8):
            t = j/7
            p = edge.lerp(outer, t)
            p.y -= (.0014 if top else .0006)*math.sin(math.pi*t)*abs(sine)
            gy = globe_y(p.x, p.z)
            if gy is not None and j < 7:
                p.y = min(p.y, gy-.00095)
            basis.data[j*64+i].co = p
            closed = p.copy()
            closed.z = (seam+(.00004 if top else -.00004))*(1-t)+outer.z*t
            closed.y = seam_y*(1-t)+outer.y*t
            closed.y -= (.005 if top else .001)*math.sin(math.pi*t)*abs(sine)
            gy = globe_y(closed.x, closed.z)
            if gy is not None and j < 7:
                closed.y = min(closed.y, gy-.001)
            blink.data[j*64+i].co = closed
    ob.data.update()
    # Existing textured skin outside the patch must also cover the globe.
    corrected = 0
    for index, vertex in enumerate(body_old.data):
        p = vertex.co
        if p.y > center.y or abs(p.x-center.x) > radius or abs(p.z-center.z) > radius:
            continue
        gy = globe_y(p.x, p.z)
        if gy is not None and p.y > gy-.0008:
            delta = gy-.0008-p.y
            for key in body.data.shape_keys.key_blocks:
                key.data[index].co.y = body_backup.shape_keys.key_blocks[key.name].data[index].co.y+delta
            corrected += 1
            report['maximum_body_adjustment_mm'] = max(report['maximum_body_adjustment_mm'], -delta*1000)
    report['body_coverage_vertices'] += corrected
    report['lids'][side] = {'vertices': len(basis.data), 'surrounding_skin_vertices_adjusted': corrected}

# Lip corners follow a continuous arc. The old tanh weighting made vertical walls.
upper = [Vector(p['world']) for p in landmarks['mouth']['upper']]
lower = [Vector(p['world']) for p in landmarks['mouth']['lower']]
midx = (upper[0].x+upper[-1].x)/2
pivot = Vector((0, -.002, 1.616))
rotation = Matrix.Rotation(math.radians(18), 3, 'X')


def jaw_rotate(p):
    return pivot+rotation@(p-pivot)


def jaw_weight(p):
    seam = (interpolate(upper, p.x).z+interpolate(lower, p.x).z)/2
    return (1-smooth((p.z-(seam-.014))/.029))*(1-smooth((p.y+.014)/.055))*smooth((p.z-1.480)/.038)


def inner_weight(sine):
    return .22+.78*(-sine)**.85 if sine < 0 else .22*(1-sine)**1.6


lips = bpy.data.objects['V363_LIPS']
preserve_mesh(lips)
basis, opened = (lips.data.shape_keys.key_blocks[name] for name in ('Basis', 'JawOpen'))
for j in range(10):
    t = j/9
    for i in range(96):
        sine = math.sin(2*math.pi*i/96)
        p = basis.data[j*96+i].co.copy()
        weight = inner_weight(sine)*(1-t)**2+jaw_weight(p)*(1-(1-t)**2)
        target = p.lerp(jaw_rotate(p), weight)
        target.x = midx+(target.x-midx)*(1-.10*(1-t)**2)
        target.z += .002*max(0., sine)*(1-t)**2
        opened.data[j*96+i].co = target
cavity = bpy.data.objects['V363_MOUTH_CAVITY']
preserve_mesh(cavity)
basis, opened = (cavity.data.shape_keys.key_blocks[name] for name in ('Basis', 'JawOpen'))
for j in range(5):
    for i in range(96):
        sine = math.sin(2*math.pi*i/96)
        p = basis.data[j*96+i].co.copy()
        target = p.lerp(jaw_rotate(p), inner_weight(sine))
        target.x = midx+(target.x-midx)*(1-.10*(1-j/4))
        target.z += .002*max(0., sine)*(1-j/4)
        opened.data[j*96+i].co = target

# The EEVEE subsurface pass was washing out the thin tongue surface.
shader = bpy.data.materials['V363_TONGUE'].node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.095, .013, .012, 1.)
shader.inputs['Subsurface Weight'].default_value = .025
shader.inputs['Subsurface Scale'].default_value = .00035
shader.inputs['Coat Weight'].default_value = .04
shader.inputs['Coat Roughness'].default_value = .32
shader.inputs['Roughness'].default_value = .55
shader.inputs['Specular IOR Level'].default_value = .25

scene.render.engine = 'BLENDER_EEVEE'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = .40


def render(name, blink=0., jaw=0., side=False):
    head['Blink.L'] = head['Blink.R'] = blink
    head['JawOpen'] = jaw
    camera = scene.camera
    camera.location = (.65, -1.25, 1.65) if side else (0, -1.4, 1.66)
    camera.rotation_euler = (Vector((0, 0, 1.65 if side else 1.66))-camera.location).to_track_quat('-Z', 'Y').to_euler()
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)


render('v364_neutral_front')
render('v364_blink_front', blink=1.)
render('v364_speaking_front', jaw=.4)
render('v364_speaking_three_quarter', jaw=.4, side=True)
head['Blink.L'] = head['Blink.R'] = head['JawOpen'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
report['rig_drivers'] = len(rig.animation_data.drivers)
(out/'deformation_repair.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_face_deformation_v364.blend'), compress=True)
print(json.dumps(report))
