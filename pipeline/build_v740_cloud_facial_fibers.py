"""Restore real brow/beard fibers, bound to this trial's facial shape keys."""
import bpy
import json
import gzip
import math
import runpy
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
cranium = runpy.run_path(str(ROOT / 'native_cranium_mapping.py'))
OUT = Path('results')
OUT.mkdir(exist_ok=True)
body = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
mesh = body.data
keys = mesh.shape_keys.key_blocks
basis = keys['Basis']
assert len(rig.animation_data.drivers) == 1957
assert not bpy.app.is_job_running('RENDER')
assert all('V740_'+kind+'_FIBERS' not in bpy.data.objects for kind in ('BROW','BEARD'))
coords = np.empty((len(mesh.vertices),3), dtype=np.float32)
basis.data.foreach_get('co', coords.ravel())
vectors = [Vector(p) for p in coords]
mesh.calc_loop_triangles()
rng = np.random.default_rng(740)
report = {}


def native_beard_mask(records, tree, surface_triangles, threshold):
    """Resample the current photo material; old samples only define growth sites."""
    image = bpy.data.images.load(str(Path('Character_An_photoreal_head_basecolor_v326.png').resolve()),
                                 check_existing=False)
    try:
        width, height = image.size
        assert width > 0 and height > 0
        pixels = np.empty(width*height*4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        pixels = pixels.reshape(height, width, 4)
        assert np.isfinite(pixels).all() and pixels[..., :3].std() > .01
        native = mesh.uv_layers['UVMap']
        repaired = mesh.uv_layers['V740_ObservedSidePhotoUV']
        blend = mesh.attributes['V740_ObservedSidePhotoBlend']

        def sample(uv):
            # Blender image rows start at the bottom, matching UV coordinates.
            x = np.clip(float(uv.x)*width-.5, 0, width-1)
            y = np.clip(float(uv.y)*height-.5, 0, height-1)
            ix, iy = int(x), int(y)
            jx, jy = min(ix+1, width-1), min(iy+1, height-1)
            fx, fy = x-ix, y-iy
            return ((1-fy)*((1-fx)*pixels[iy,ix,:3]+fx*pixels[iy,jx,:3])
                    + fy*((1-fx)*pixels[jy,ix,:3]+fx*pixels[jy,jx,:3]))

        updated = []
        for record in records:
            x, _, z = record['point']
            hit, normal, index, _ = tree.ray_cast(Vector((x,-.5,z)), Vector((0,1,0)))
            if hit is None or normal.y > -.10:
                continue
            triangle = surface_triangles[index]
            a, b, c = coords[list(triangle.vertices)].astype(np.float64)
            edge_b, edge_c = b-a, c-a
            normal64 = np.cross(edge_b, edge_c)
            denom = float(normal64 @ normal64)
            if denom < 1e-24:
                continue
            offset = np.asarray(hit, dtype=np.float64)-a
            v = float(np.cross(offset, edge_c) @ normal64)/denom
            w = float(np.cross(edge_b, offset) @ normal64)/denom
            bary = (1-v-w, v, w)
            if not all(math.isfinite(v) and -.01 <= v <= 1.01 for v in bary):
                continue
            colors = []
            for layer in (native, repaired):
                uv = sum((layer.data[i].uv * weight for i, weight in zip(triangle.loops, bary)),
                         Vector((0,0)))
                colors.append(sample(uv))
            weight = sum(blend.data[i].value*b for i,b in zip(triangle.vertices,bary))
            rgb = colors[0]*(1-weight)+colors[1]*weight
            updated.append(dict(record, luma=float(rgb @ np.array((.2126,.7152,.0722)))))

        def eligible(items):
            return {region: sum(r['luma'] < threshold and predicate(r['point']) for r in items)
                    for region, predicate in {
                        'all': lambda p: True,
                        'moustache': lambda p: abs(p[0]) < .033 and p[2] > 1.579,
                        'chin': lambda p: abs(p[0]) < .025 and p[2] < 1.56,
                    }.items()}
        return updated, {'source': 'current native UV photo with observed-side repair blend',
                         'historical_eligible': eligible(records), 'native_eligible': eligible(updated),
                         'projection_rejected': len(records)-len(updated),
                         'growth_sites_and_lip_nose_exclusions': 'historical; unchanged'}
    finally:
        bpy.data.images.remove(image)


for kind, sample_file, threshold, per_side, steps, z_low, z_high in [
    ('BROW','v740_brow_growth.json.gz',.44,1900,7,1.645,1.700),
    ('BEARD','v740_beard_growth.json.gz',.43,6500,6,1.495,1.625),
]:
    surface_triangles = [t for t in mesh.loop_triangles
                         if all(z_low < coords[i,2] < z_high and coords[i,1] < -.025 for i in t.vertices)]
    triangles = [tuple(t.vertices) for t in surface_triangles]
    bvh = BVHTree.FromPolygons(vectors,triangles,all_triangles=True)
    records = json.loads(gzip.decompress((ROOT/sample_file).read_bytes()))
    mask_report = {'source': 'historical brow mask'}
    if kind == 'BEARD':
        records, mask_report = native_beard_mask(records, bvh, surface_triangles, threshold)
    selected = []
    for side in ('L','R'):
        candidates = [r for r in records if r['side']==side and r['luma']<threshold]
        assert candidates, f'No eligible {kind} candidates on {side}'
        probabilities = np.array([max(.01,(threshold-r['luma'])/threshold) for r in candidates])
        indices = rng.choice(len(candidates),min(per_side,len(candidates)),replace=False,
                             p=probabilities/probabilities.sum())
        selected.extend(candidates[i] for i in indices)
    points, faces, attachments, weights = [], [], [], []
    counts = {'L':0,'R':0}
    for record in selected:
        # Historical sample indices predate topology cleanup. Use their X/Z
        # growth region, then reproject every point onto this trial's Basis.
        root = Vector(record['point'])
        if kind == 'BROW':
            # Growth samples are pre-compression donor coordinates; use the
            # same final field as the restored native face, not V739's old field.
            root.z = float(cranium['compress'](root.z, cranium['TRIAL_REDUCTION']))
        sign = 1. if root.x > 0 else -1.
        u = min(1.,max(0.,(abs(root.x)-.016)/.050))
        if kind == 'BROW':
            direction = Vector((sign*(.32+.68*u),0.,.95-1.30*u)).normalized()
            length = rng.uniform(.0030,.0052)*(1.-.22*u)
            radius = rng.uniform(.000025,.000040)
        else:
            mustache = root.z > 1.579
            direction = Vector((sign*(.6 if mustache else .2),0.,-1.)).normalized()
            length = rng.uniform(.0030,.0048) if mustache else rng.uniform(.0024,.0047)
            radius = rng.uniform(.000030,.000050)
        centers, normals, samples = [], [], []
        for j in range(steps):
            t = j/(steps-1.)
            target = root+direction*(length*t)
            hit,normal,index,_ = bvh.ray_cast(Vector((target.x,-.5,target.z)),Vector((0,1,0)))
            if hit is None or normal.y > -.10:
                break
            ids = triangles[index]
            # Compute in float64 after translating to the triangle origin.
            # Tiny facial triangles lose precision in the float32 transform.
            a, b, c = coords[list(ids)].astype(np.float64)
            edge_b, edge_c = b-a, c-a
            normal64 = np.cross(edge_b, edge_c)
            denom = float(normal64 @ normal64)
            if denom < 1e-24:
                break
            offset64 = np.asarray(hit, dtype=np.float64)-a
            v = float(np.cross(offset64, edge_c) @ normal64)/denom
            w = float(np.cross(edge_b, offset64) @ normal64)/denom
            bary = np.array((1.-v-w, v, w), dtype=np.float64)
            if not np.isfinite(bary).all() or bary.min() < -.01 or bary.max() > 1.01:
                break
            if np.linalg.norm(bary @ np.array((a,b,c))-np.asarray(hit)) > 2e-6:
                break
            height = .000055+.00027*math.sin(math.pi*t)+.00007*t if kind=='BROW' else .00007+.00048*math.sin(math.pi*t)+.00035*t
            centers.append(hit+normal*height)
            normals.append(normal)
            samples.append((ids,bary))
        if len(centers) != steps:
            continue
        offset = len(points)
        for j,(center,normal,(ids,bary)) in enumerate(zip(centers,normals,samples)):
            t = j/(steps-1.)
            tangent = (centers[min(j+1,steps-1)]-centers[max(0,j-1)]).normalized()
            across = tangent.cross(normal).normalized()
            perpendicular = across.cross(tangent).normalized()
            width = max(.000003,radius*(1.-.93*t**1.3))
            for k in range(3):
                angle = k*math.tau/3
                points.append(center+width*(math.cos(angle)*perpendicular+math.sin(angle)*across))
                attachments.append(ids)
                weights.append(bary[:])
            if j:
                for k in range(3):
                    faces.append((offset+(j-1)*3+k,offset+(j-1)*3+(k+1)%3,
                                  offset+j*3+(k+1)%3,offset+j*3+k))
        counts[record['side']] += 1
    assert min(counts.values()) > 0, f'No fibers on one side: {kind} {counts}'
    assert np.isfinite(np.asarray(points)).all()
    assert np.allclose(np.asarray(weights).sum(axis=1), 1, atol=1e-5)
    name = 'V740_'+kind+'_FIBERS'
    data = bpy.data.meshes.new(name)
    data.from_pydata(points,[],faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_set(True)
    obj.hide_render = True
    obj.shape_key_add(name='Basis')
    pts = np.asarray(points,dtype=np.float32)
    attach = np.asarray(attachments,dtype=np.int32)
    barys = np.asarray(weights,dtype=np.float32)
    source_co = np.empty_like(coords)
    for source in list(keys)[1:]:
        source.data.foreach_get('co',source_co.ravel())
        delta = ((source_co[attach]-coords[attach])*barys[:,:,None]).sum(axis=1)
        key = obj.shape_key_add(name=source.name)
        key.value = 0.
        key.data.foreach_set('co',(pts+delta).ravel())
        key.slider_min, key.slider_max = source.slider_min, source.slider_max
        driver = key.driver_add('value').driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name,var.type = 'v','SINGLE_PROP'
        var.targets[0].id_type = 'KEY'
        var.targets[0].id = mesh.shape_keys
        var.targets[0].data_path = source.path_from_id('value')
        driver.expression = 'v'
    mat = bpy.data.materials.new(name+'_MATERIAL')
    mat.use_nodes = True
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (.006,.0035,.002,1.)
    shader.inputs['Roughness'].default_value = .55 if kind=='BROW' else .65
    shader.inputs['Specular IOR Level'].default_value = .20
    data.materials.append(mat)
    for polygon in data.polygons:
        polygon.use_smooth = True
    bone = rig.pose.bones['DEF-Head']
    frame = rig.matrix_world @ bone.matrix @ Matrix.Translation((0,bone.bone.length,0))
    obj.parent,obj.parent_type,obj.parent_bone = rig,'BONE','DEF-Head'
    obj.matrix_parent_inverse = frame.inverted()
    obj.matrix_basis = Matrix.Identity(4)
    obj['surface_attachment'] = 'V740 native face barycentric shape-key deformation plus DEF-Head parent'
    report[kind] = {'fiber_counts':counts,'vertices':len(points),'shape_keys':len(keys),
                    'key_drivers':len(data.shape_keys.animation_data.drivers), 'growth_mask':mask_report}
rig.update_tag(refresh={'OBJECT'})
bpy.context.view_layer.update()
assert len(rig.animation_data.drivers) == 1957
(OUT/'facial_fibers_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))

scene = bpy.data.scenes['V739_NATIVE_FACE_INSPECTION']
for name in ('V740_BROW_FIBERS', 'V740_BEARD_FIBERS'):
    obj = bpy.data.objects[name]
    if obj.name not in scene.objects:
        scene.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_set(False)
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'V740_cloud_groom_trial.blend').resolve()), compress=True)
