"""Add surface-following brow fibers, lip volume and a continuous neck shader."""
from pathlib import Path
import json
import math
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v383_face_detail'
OUT.mkdir(exist_ok=True)
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mesh = body.data
keys = mesh.shape_keys.key_blocks
basis = keys['Basis']
assert len(rig.animation_data.drivers) == 1957
assert not body.get('V383_face_detail_applied')
assert bpy.data.objects.get('V383_BROW_FIBERS') is None
report = {}

# Match the unmodified scan at the neck boundary, then blend every changed
# skin property over the same 40 mm transition used by the albedo correction.
original = mesh.materials[0].node_tree.nodes['Principled BSDF']
backup = {}
for name in ('V372_FACE_SKIN','V377_REFERENCE_PHOTO_SKIN'):
    mat = bpy.data.materials[name]
    nodes,links = mat.node_tree.nodes,mat.node_tree.links
    shader = nodes['Principled BSDF']
    attr = nodes.new('ShaderNodeAttribute')
    attr.name = 'V383_NeckTransition'
    attr.attribute_name = 'V372_HeadSkin'
    backup[name] = {}
    for socket in ('Roughness','Specular IOR Level','Subsurface Weight'):
        old = float(shader.inputs[socket].default_value)
        base = float(original.inputs[socket].default_value)
        assert not shader.inputs[socket].is_linked
        backup[name][socket] = {'base':base,'skin':old}
        blend = nodes.new('ShaderNodeMath')
        blend.name = 'V383_'+socket.replace(' ','_')
        blend.operation = 'MULTIPLY_ADD'
        blend.inputs[1].default_value = old-base
        blend.inputs[2].default_value = base
        links.new(attr.outputs['Fac'],blend.inputs[0])
        links.new(blend.outputs[0],shader.inputs[socket])
    for bump in [n for n in nodes if n.type=='BUMP']:
        if bump.inputs['Strength'].is_linked:
            continue
        blend = nodes.new('ShaderNodeMath')
        blend.operation = 'MULTIPLY'
        blend.inputs[1].default_value = bump.inputs['Strength'].default_value
        links.new(attr.outputs['Fac'],blend.inputs[0])
        links.new(blend.outputs[0],bump.inputs['Strength'])
report['neck_materials'] = backup

# Add a small rolled vermilion volume, leaving both aperture and outer join
# fixed. Applying the same displacement to all keys preserves their deltas.
lips = bpy.data.objects['V363_LIPS']
lip_keys = lips.data.shape_keys.key_blocks
lip_backup = {k.name:[list(v.co) for v in k.data] for k in lip_keys}
peak = 0.
for j in range(10):
    profile = math.sin(math.pi*j/9.)**2 if 0<j<9 else 0.
    for i in range(96):
        side = math.sin(i*math.tau/96.)
        depth = (.00060 if side>0 else .00090)*profile*abs(side)**.55
        for key in lip_keys:
            key.data[j*96+i].co.y -= depth
        peak = max(peak,depth)
lips.data.update()
report['lip_forward_volume_mm'] = peak*1000.
report['lip_aperture_change_mm'] = max(
    (v.co-Vector(lip_backup['Basis'][i])).length*1000.
    for i,v in enumerate(lip_keys['Basis'].data[:96]))
assert report['lip_aperture_change_mm'] == 0.
(OUT/'before_lip_detail.json').write_text(json.dumps(lip_backup))

# Each fiber point carries the barycentric expression motion of the actual
# facial surface below it. Head parenting alone would leave brows behind
# when a brow expression changes the skin.
mesh.calc_loop_triangles()
triangles = [t for t in mesh.loop_triangles
             if all(1.650<basis.data[i].co.z<1.695 and basis.data[i].co.y<-.025
                    for i in t.vertices)]
coords = [v.co.copy() for v in basis.data]
bvh = BVHTree.FromPolygons(coords,[list(t.vertices) for t in triangles],all_triangles=True)
records = json.loads((OUT/'brow_samples.json').read_text())
rng = np.random.default_rng(383)
selected = []
for side in ('L','R'):
    candidates = [r for r in records if r['side']==side and r['luma']<.32]
    probabilities = np.asarray([max(.01,(.32-r['luma'])/.32) for r in candidates])
    ids = rng.choice(len(candidates),size=min(950,len(candidates)),replace=False,
                     p=probabilities/probabilities.sum())
    selected.extend(candidates[i] for i in ids)

points,faces,attachments = [],[],[]
steps,sides = 7,3
fiber_counts = {'L':0,'R':0}
for record in selected:
    root = Vector(record['point'])
    sign = 1. if root.x>0 else -1.
    u = min(1.,max(0.,(abs(root.x)-.016)/.050))
    direction = Vector((sign*(.32+.68*u),0.,.95-1.30*u)).normalized()
    length = rng.uniform(.0030,.0052)*(1.-.22*u)
    radius = rng.uniform(.000025,.000040)
    centers,normals,samples = [],[],[]
    for j in range(steps):
        t = j/(steps-1.)
        target = root+direction*(length*t)
        hit,normal,index,_ = bvh.ray_cast(Vector((target.x,-.5,target.z)),Vector((0,1,0)))
        if hit is None or normal.y>-.10:
            break
        ids = list(triangles[index].vertices)
        weights = barycentric_transform(hit,*[coords[i] for i in ids],
                                         Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        center = hit+normal*(.000055+.00027*math.sin(math.pi*t)+.00007*t)
        centers.append(center)
        normals.append(normal)
        samples.append((ids,weights))
    if len(centers)!=steps:
        continue
    offset = len(points)
    for j,(center,normal,sample) in enumerate(zip(centers,normals,samples)):
        t = j/(steps-1.)
        tangent = (centers[min(j+1,steps-1)]-centers[max(0,j-1)]).normalized()
        across = tangent.cross(normal).normalized()
        perpendicular = across.cross(tangent).normalized()
        width = max(.000003,radius*(1.-.93*t**1.3))
        for k in range(sides):
            angle = k*math.tau/sides
            points.append(center+width*(math.cos(angle)*perpendicular+math.sin(angle)*across))
            attachments.append(sample)
        if j:
            for k in range(sides):
                faces.append((offset+(j-1)*sides+k,offset+(j-1)*sides+(k+1)%sides,
                              offset+j*sides+(k+1)%sides,offset+j*sides+k))
    fiber_counts[record['side']] += 1

data = bpy.data.meshes.new('V383_BROW_FIBERS')
data.from_pydata(points,[],faces)
data.update()
obj = bpy.data.objects.new('V383_BROW_FIBERS',data)
bpy.context.scene.collection.objects.link(obj)
obj.shape_key_add(name='Basis')
for source in list(keys)[1:]:
    key = obj.shape_key_add(name=source.name)
    for i,(ids,weights) in enumerate(attachments):
        delta = sum(((source.data[vi].co-basis.data[vi].co)*w
                     for vi,w in zip(ids,weights)),Vector())
        key.data[i].co = points[i]+delta
    driver = key.driver_add('value').driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name,var.type = 'v','SINGLE_PROP'
    var.targets[0].id_type = 'KEY'
    var.targets[0].id = body.data.shape_keys
    var.targets[0].data_path = source.path_from_id('value')
    driver.expression = 'v'
mat = bpy.data.materials.new('V383_BROW_HAIR')
mat.use_nodes = True
shader = mat.node_tree.nodes['Principled BSDF']
shader.inputs['Base Color'].default_value = (.009,.005,.0028,1.)
shader.inputs['Roughness'].default_value = .38
shader.inputs['Specular IOR Level'].default_value = .30
data.materials.append(mat)
for polygon in data.polygons:
    polygon.use_smooth = True
bone = rig.pose.bones['DEF-Head']
frame = rig.matrix_world@bone.matrix@Matrix.Translation((0,bone.bone.length,0))
obj.parent,obj.parent_type,obj.parent_bone = rig,'BONE','DEF-Head'
obj.matrix_parent_inverse = frame.inverted()
obj.matrix_basis = Matrix.Identity(4)
obj['surface_attachment'] = 'Barycentric body shape keys plus DEF-Head parent'
report['brow_fibers'] = fiber_counts
report['brow_shape_keys'] = [k.name for k in data.shape_keys.key_blocks]
report['brow_vertices'] = len(data.vertices)
report['rig_drivers'] = len(rig.animation_data.drivers)
assert report['rig_drivers'] == 1957
body['V383_face_detail_applied'] = True
mesh.update()
rig.update_tag()
bpy.context.view_layer.update()
(OUT/'face_detail_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
