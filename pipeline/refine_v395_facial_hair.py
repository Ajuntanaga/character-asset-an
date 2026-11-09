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
OUT = ROOT/'production_v395_facial_hair'
OUT.mkdir(exist_ok=True)
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mesh = body.data
keys = mesh.shape_keys.key_blocks
basis = keys['Basis']
assert len(rig.animation_data.drivers) == 1957
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.objects.get('V395_BEARD_FIBERS') is None
report = {}
# Each fiber point carries the barycentric expression motion of the actual
# facial surface below it. Head parenting alone would leave brows behind
# when a brow expression changes the skin.
mesh.calc_loop_triangles()
triangles = [t for t in mesh.loop_triangles
             if all(1.505<basis.data[i].co.z<1.615 and basis.data[i].co.y<-.025
                    for i in t.vertices)]
coords = [v.co.copy() for v in basis.data]
bvh = BVHTree.FromPolygons(coords,[list(t.vertices) for t in triangles],all_triangles=True)
records = json.loads((OUT/'beard_samples.json').read_text())
rng = np.random.default_rng(383)
selected = []
for side in ('L','R'):
    candidates = [r for r in records if r['side']==side and r['luma']<.25]
    probabilities = np.asarray([max(.01,(.25-r['luma'])/.25) for r in candidates])
    ids = rng.choice(len(candidates),size=min(4000,len(candidates)),replace=False,
                     p=probabilities/probabilities.sum())
    selected.extend(candidates[i] for i in ids)

points,faces,attachments = [],[],[]
steps,sides = 5,3
fiber_counts = {'L':0,'R':0}
for record in selected:
    root = Vector(record['point'])
    sign = 1. if root.x>0 else -1.
    u = min(1.,max(0.,(abs(root.x)-.016)/.050))
    mustache = root.z>1.579
    direction = Vector((sign*(.6 if mustache else .2),0.,-1.)).normalized()
    length = rng.uniform(.0018,.0032) if mustache else rng.uniform(.0007,.0016)
    radius = rng.uniform(.000030,.000050)
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
        center = hit+normal*(.00006+.00020*math.sin(math.pi*t)+.00016*t)
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

data = bpy.data.meshes.new('V395_BEARD_FIBERS')
data.from_pydata(points,[],faces)
data.update()
obj = bpy.data.objects.new('V395_BEARD_FIBERS',data)
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
mat = bpy.data.materials.new('V395_BEARD_HAIR')
mat.use_nodes = True
shader = mat.node_tree.nodes['Principled BSDF']
shader.inputs['Base Color'].default_value = (.009,.005,.0028,1.)
shader.inputs['Roughness'].default_value = .50
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
report['beard_fibers'] = fiber_counts
report['beard_shape_keys'] = [k.name for k in data.shape_keys.key_blocks]
report['beard_vertices'] = len(data.vertices)
report['rig_drivers'] = len(rig.animation_data.drivers)
assert report['rig_drivers'] == 1957
bpy.context.view_layer.update()
(OUT/'facial_hair_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_facial_hair_v395.blend'),compress=True)
print(json.dumps(report))
