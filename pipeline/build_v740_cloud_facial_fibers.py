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
# Derive smooth normals from Basis, matching the projection geometry exactly.
# Flat BVH normals jump at triangle boundaries and kink lifted fiber samples.
basis_triangles = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
triangle_points = coords[basis_triangles].astype(np.float64)
area_normals = np.cross(triangle_points[:, 1]-triangle_points[:, 0],
                        triangle_points[:, 2]-triangle_points[:, 0])
basis_normals = np.zeros(coords.shape, dtype=np.float64)
for corner in range(3):
    np.add.at(basis_normals, basis_triangles[:, corner], area_normals)
basis_normals /= np.maximum(np.linalg.norm(basis_normals, axis=1, keepdims=True), 1e-20)
rng = np.random.default_rng(740)
report = {}


def native_photo_mask(records, tree, surface_triangles, threshold):
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
        # Separate projection loss from photo eligibility in the visibly sparse
        # cheek region. Counts include historical and supplemental sites.
        cheek_regions = {}
        for side in ('L', 'R'):
            def in_cheek(r):
                x, _, z = r['point']
                return r['side'] == side and .035 <= abs(x) <= .080 and 1.590 <= z <= 1.625
            original = [r for r in records if in_cheek(r)]
            projected = [r for r in updated if in_cheek(r)]
            cheek_regions[side] = {
                'sites': len(original),
                'projected': len(projected),
                'projection_rejected': len(original)-len(projected),
                'photo_eligible': sum(r['luma'] < threshold for r in projected),
            }
        return updated, {'source': 'current native UV photo with observed-side repair blend',
                         'cheek_regions': cheek_regions,
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
    if kind == 'BROW':
        # Move historical growth sites into the final face field before both
        # texture sampling and surface projection; apply compression only once.
        records = [dict(r, point=[r['point'][0], r['point'][1],
                   float(cranium['compress'](r['point'][2], cranium['TRIAL_REDUCTION']))])
                   for r in records]
        records, mask_report = native_photo_mask(records, bvh, surface_triangles, threshold)
        mask_report['growth_sites_and_lip_nose_exclusions'] = (
            'historical brow sites mapped into final native face; current photo eligibility')
    if kind == 'BEARD':
        # Add native-projected moustache sites without moving the established
        # lip/nose boundary or increasing cheek/jaw sampling density.
        growth_rng = np.random.default_rng(741)
        historical_count = len(records)
        for x, z in growth_rng.uniform((-.033, 1.579), (.033, 1.598), (4000, 2)):
            if abs(x) < .001:
                continue
            if ((x/.039)**2+((z-1.571)/.011)**2) < 1.15:
                continue
            if z > 1.588 and abs(x) < .025:
                continue
            records.append({'side': 'L' if x > 0 else 'R',
                            'point': [float(x), -.5, float(z)], 'luma': 1.0})
        extra_sites = len(records)-historical_count
        # Historical beard sites stop at z=1.600: the upper cheek portion of
        # the native surface otherwise cannot grow fibers, whatever its mask.
        # Keep the central lip/nose area excluded and retain photo eligibility.
        cheek_rng = np.random.default_rng(752)
        cheek_sites = 0
        for x, z in cheek_rng.uniform((.035, 1.590), (.080, 1.625), (4000, 2)):
            for sign, side in ((1., 'L'), (-1., 'R')):
                records.append({'side': side,
                                'point': [float(sign*x), -.5, float(z)], 'luma': 1.0})
                cheek_sites += 1
        records, mask_report = native_photo_mask(records, bvh, surface_triangles, threshold)
        mask_report['supplemental_moustache_sites'] = extra_sites
        mask_report['supplemental_cheek_sites'] = cheek_sites
        mask_report['growth_sites_and_lip_nose_exclusions'] = (
            'historical sites plus native-projected moustache and lateral cheek samples; central lip/nose exclusions retained')
    if kind == 'BEARD':
        # Trial cheek line rises from the mouth corner toward the sideburn.
        # Photo darkness modulates density inside this envelope; it must not
        # turn lighting differences into bald patches or nose-side islands.
        for record in records:
            x, _, z = record['point']
            lateral = abs(x)
            if lateral >= .033:
                edge = float(np.interp(lateral, [.033, .050, .080],
                                       [1.585, 1.602, 1.625]))
                fade = min(1., max(0., (edge-z)/.004))
                fade = fade*fade*(3.-2.*fade)
                photo = max(0., (threshold-record['luma'])/threshold)
                record['density'] = fade*(.30+.70*photo)
            elif z > 1.598:
                # Historical dark samples include nose-side/under-eye islands.
                # The moustache seed region ends here; central skin above it
                # is outside the beard even when the photo contains shadows.
                record['density'] = 0.
            else:
                # Preserve the established moustache and lip exclusions.
                record['density'] = (max(.01, (threshold-record['luma'])/threshold)
                                     if record['luma'] < threshold else 0.)
        mask_report['cheek_envelope_trial'] = {
            'x_z_knots': [[.033, 1.585], [.050, 1.602], [.080, 1.625]],
            'feather_m': .004, 'photo_density_floor': .30,
            'eligible_by_side': {side: sum(r['side'] == side and r['density'] > 0
                                           for r in records) for side in ('L', 'R')},
        }
    selected = []
    for side in ('L','R'):
        candidates = [r for r in records if r['side']==side and
                      (r['density'] > 0 if kind == 'BEARD' else r['luma'] < threshold)]
        assert candidates, f'No eligible {kind} candidates on {side}'
        probabilities = np.array([r['density'] if kind == 'BEARD' else
                                  max(.01,(threshold-r['luma'])/threshold) for r in candidates])
        indices = rng.choice(len(candidates),min(per_side,len(candidates)),replace=False,
                             p=probabilities/probabilities.sum())
        selected.extend(candidates[i] for i in indices)
    points, faces, attachments, weights = [], [], [], []
    counts = {'L':0,'R':0}
    shaft_lengths = {}
    length_fit_rejected = 0
    for record in selected:
        # Historical sample indices predate topology cleanup. Use their X/Z
        # growth region, then reproject every point onto this trial's Basis.
        root = Vector(record['point'])
        sign = 1. if root.x > 0 else -1.
        u = min(1.,max(0.,(abs(root.x)-.016)/.050))
        if kind == 'BROW':
            direction = Vector((sign*(.32+.68*u),0.,.95-1.30*u)).normalized()
            length = rng.uniform(.0030,.0052)*(1.-.22*u)
            radius = rng.uniform(.000040,.000060)
        else:
            mustache = root.z > 1.579 and abs(root.x) < .033
            direction = Vector((sign*(.6 if mustache else .2),0.,-1.)).normalized()
            if mustache:
                length = rng.uniform(.0030,.0048)
            else:
                # Close-trimmed chin with the existing shorter lateral stubble.
                cheek = min(1., max(0., (abs(root.x)-.025)/.020))
                length = rng.uniform(.0024,.0040)*(.50-.15*cheek)
            radius = rng.uniform(.000040,.000065)
        # X/Z distance is not surface arclength, especially below the chin.
        # Reproject a shorter/longer span, retaining real triangle bindings at
        # every sample instead of scaling finished shafts away from the skin.
        projected_length = length
        length_fit_ok = False
        for length_iteration in range(8 if kind == 'BEARD' else 1):
            centers, normals, samples = [], [], []
            for j in range(steps):
                t = j/(steps-1.)
                target = root+direction*(projected_length*t)
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
                smooth_normal = Vector(bary @ basis_normals[list(ids)])
                if smooth_normal.length_squared < 1e-12:
                    break
                smooth_normal.normalize()
                if smooth_normal.dot(normal) <= 0:
                    break
                normal = smooth_normal
                if kind == 'BROW':
                    height = .000055+.00027*math.sin(math.pi*t)+.00007*t
                else:
                    # Short beard shafts follow the face with a gentle tip lift.
                    # The previous arch peaked near 0.74 mm; reduce its suspected
                    # contribution to doubled strokes in the resolved preview.
                    height = .00007 + .00012*t
                centers.append(hit+normal*height)
                normals.append(normal)
                samples.append((ids,bary))
            if len(centers) != steps:
                break
            measured = sum((b-a).length for a,b in zip(centers, centers[1:]))
            if kind == 'BROW' or abs(measured-length) <= length*.03:
                length_fit_ok = True
                break
            projected_length *= max(.2, min(2., length/max(measured, 1e-9)))
        if not length_fit_ok:
            length_fit_rejected += 1
            continue
        region = ('brow' if kind == 'BROW' else 'moustache' if mustache
                  else 'chin' if abs(root.x) < .025 else 'cheek_jaw')
        actual_length = sum((b-a).length for a,b in zip(centers, centers[1:]))
        shaft_lengths.setdefault(region, []).append((length, actual_length))
        offset = len(points)
        for j,(center,normal,(ids,bary)) in enumerate(zip(centers,normals,samples)):
            t = j/(steps-1.)
            tangent = (centers[min(j+1,steps-1)]-centers[max(0,j-1)]).normalized()
            across = tangent.cross(normal).normalized()
            perpendicular = across.cross(tangent).normalized()
            # Keep a full shaft; concentrate taper near the distal tip.
            width = max(.000003,radius*(1.-.95*t**4.0))
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
                    'surface_length_fit': {'method': 'iterative_reprojection' if kind == 'BEARD' else 'unchanged_brow',
                                           'tolerance_fraction': .03 if kind == 'BEARD' else None,
                                           'rejected': length_fit_rejected},
                    'shaft_lengths_by_region': {region: {
                        'count': len(values),
                        'target_mm_p50_p95_max': (np.percentile(np.array(values)[:,0], [50,95,100])*1000).tolist(),
                        'actual_mm_p50_p95_max': (np.percentile(np.array(values)[:,1], [50,95,100])*1000).tolist(),
                        'stretch_ratio_p50_p95_max': np.percentile(np.array(values)[:,1]/np.array(values)[:,0], [50,95,100]).tolist(),
                    } for region,values in shaft_lengths.items()},
                    'key_drivers':len(data.shape_keys.animation_data.drivers), 'growth_mask':mask_report,
                    'shaft_radius_m': [.000040, .000060 if kind=='BROW' else .000065],
                    'taper': {'amount': .95, 'exponent': 4.0},
                    'surface_lift_profile': ('arched_brow' if kind=='BROW' else 'monotonic_beard_70_to_190_um'),
                    'surface_normals': 'barycentric area-weighted Basis vertex normals'}
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
