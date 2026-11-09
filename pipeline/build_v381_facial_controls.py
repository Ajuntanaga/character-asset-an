"""Transfer donor-relative expressions while retaining the current face and jaw."""
from pathlib import Path
import json
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v381_facial_controls'
OUT.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
lips = bpy.data.objects['V363_LIPS']
cavity = bpy.data.objects['V363_MOUTH_CAVITY']
donor = bpy.data.objects['V376_FACE_PHOTO_DONOR']
assert len(rig.animation_data.drivers) == 1957
assert not body.get('V381_expression_transfer_applied')
assert len(lips.data.vertices) == 960 and len(cavity.data.vertices) == 480
controls = {
    'Smile.L':'mouthSmileLeft', 'Smile.R':'mouthSmileRight',
    'BrowDown.L':'browDownLeft', 'BrowDown.R':'browDownRight',
    'BrowOuterUp.L':'browOuterUpLeft', 'BrowOuterUp.R':'browOuterUpRight',
}
assert not set(controls).intersection(body.data.shape_keys.key_blocks.keys())
data = json.loads((ROOT/'production_v376_face_refinement/photo_donor_geometry.json').read_text())
source_z = [-1.72,-.85,-.30,.0515203,.33,.52,.80,.94,1.3065]
target_z = [1.435,1.521,1.571,1.609121,1.645,1.670,1.709,1.732,1.795]


def fitted(p):
    return Vector((.123*p.x+.0016, .121*p.y+.00802,
                   float(np.interp(p.z,source_z,target_z))))


def smooth(t):
    t = max(0.,min(1.,t))
    return t*t*(3.-2.*t)


donor_keys = donor.data.shape_keys.key_blocks
coords = [fitted(donor.matrix_world@v.co) for v in donor_keys['Basis'].data]
triangles = data['triangles']
bvh = BVHTree.FromPolygons(coords,triangles,all_triangles=True)
fields = {name:[fitted(donor.matrix_world@v.co)-p
                for v,p in zip(donor_keys[source].data,coords)]
          for name,source in controls.items()}
lid_index = list(body.data.materials).index(bpy.data.materials['V365_LID_SKIN'])
excluded = {v for p in body.data.polygons if p.material_index == lid_index
            for v in p.vertices}


def sample(p):
    weight = smooth((p.z-1.50)/.020)*smooth((1.732-p.z)/.018)
    weight *= smooth((.086-abs(p.x))/.016)*smooth((-.022-p.y)/.040)
    for cx in (.038,-.0355):
        distance = math.hypot((p.x-cx)/.022,(p.z-1.645)/.012)
        weight *= smooth((distance-1.)/.48)
    if weight < 1e-5:
        return None
    hit,normal,index,_ = bvh.ray_cast(Vector((p.x,-.4,p.z)),Vector((0,1,0)))
    # A lip's frontmost tangent can be nearly horizontal at its rolled edge.
    # Retain those visible hits; the tighter photo-UV normal cutoff drops one.
    if hit is None or abs(hit.y-p.y) > .042 or normal.y > -.02:
        return None
    ids = triangles[index]
    weights = barycentric_transform(hit,*[coords[i] for i in ids],
                                    Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    return ids,weights,weight


def delta(field,hit):
    ids,weights,weight = hit
    return sum((field[i]*w for i,w in zip(ids,weights)),Vector())*weight


def add_key(obj,name,deltas):
    key = obj.shape_key_add(name=name,from_mix=False)
    basis = obj.data.shape_keys.key_blocks['Basis']
    inverse = obj.matrix_world.inverted().to_3x3()
    for index,d in deltas.items():
        key.data[index].co = basis.data[index].co+inverse@d
    key.slider_min,key.slider_max = 0.,1.
    driver = key.driver_add('value').driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name,var.type = 'v','SINGLE_PROP'
    var.targets[0].id = rig
    var.targets[0].data_path = 'pose.bones["Head"]["'+name+'"]'
    driver.expression = 'v'
    obj.data.update()


report = {'controls':{},'cavity_seam_max_delta_difference_mm':{},
          'excluded_lid_vertices':len(excluded)}
samples = {}
for obj in (body,lips):
    basis = obj.data.shape_keys.key_blocks['Basis']
    samples[obj.name] = {i:hit for i,v in enumerate(basis.data)
                         if not (obj == body and i in excluded)
                         if (hit := sample(obj.matrix_world@v.co)) is not None}

for name,field in fields.items():
    head[name] = 0.
    head.id_properties_ui(name).update(min=0.,max=1.,description='Photo donor relative '+name)
    deltas = {i:delta(field,hit) for i,hit in samples[body.name].items()}
    peak = max(d.length for d in deltas.values())
    assert 0.0001 < peak < .030, (name,peak)
    add_key(body,name,deltas)
    report['controls'][name] = {'source':controls[name],
                              'body_moved_vertices':sum(d.length>1e-5 for d in deltas.values()),
                              'peak_displacement_mm':peak*1000}
    if not name.startswith('Smile.'):
        continue
    lip_deltas = {i:delta(field,hit) for i,hit in samples[lips.name].items()}
    assert all(i in lip_deltas for i in range(96)), 'Missing lip-aperture sample'
    add_key(lips,name,lip_deltas)
    # Shared aperture deltas are exact. Fade only into the deep oral shell.
    cavity_deltas = {j*96+i:lip_deltas[i]*(1.-j*.5) for j in (0,1) for i in range(96)}
    add_key(cavity,name,cavity_deltas)
    lip_key = lips.data.shape_keys.key_blocks[name]
    cavity_key = cavity.data.shape_keys.key_blocks[name]
    lb = lips.data.shape_keys.key_blocks['Basis']
    cb = cavity.data.shape_keys.key_blocks['Basis']
    seam_error = max((lips.matrix_world.to_3x3()@(lip_key.data[i].co-lb.data[i].co)
                      -cavity.matrix_world.to_3x3()@(cavity_key.data[i].co-cb.data[i].co)).length
                     for i in range(96))
    assert seam_error < 3e-7
    report['cavity_seam_max_delta_difference_mm'][name] = seam_error*1000

body['V381_expression_transfer_applied'] = True
rig.update_tag()
bpy.context.view_layer.update()
assert len(rig.animation_data.drivers) == 1957
report['rig_drivers'] = len(rig.animation_data.drivers)
report['body_shape_keys'] = list(body.data.shape_keys.key_blocks.keys())
(OUT/'facial_controls_report.json').write_text(json.dumps(report,indent=2))
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = .37
scene.camera.location = (0,-1.4,1.66)
scene.camera.rotation_euler = (Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
saved_controls = {name:head[name] for name in (*controls,'JawOpen','Blink.L','Blink.R')}
try:
    head['Smile.L'] = head['Smile.R'] = .75
    head['JawOpen'] = .45
    head['Blink.L'] = head['Blink.R'] = 0.
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(OUT/'v381_smile_jaw_front.png')
    bpy.ops.render.render(write_still=True)
finally:
    for name,value in saved_controls.items():
        head[name] = value
    rig.update_tag()
    bpy.context.view_layer.update()
print(json.dumps(report))
