"""Build tighter, finer reference curls; preserve older grooms hidden for rollback."""
from collections import defaultdict
from pathlib import Path
import bisect
import json
import math
import random
import time
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import gzip

def build(root, out, *, coherent=False):
    version = "V546" if coherent else "V544"
    assert not bpy.app.is_job_running('RENDER')
    started = time.monotonic()
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert len(rig.animation_data.drivers) == 1957
    assert bpy.data.objects.get(version + '_CURL_GROOM') is None
    source = json.loads(gzip.decompress((root/'github_assets/groom/scalp_surface.json.gz').read_bytes()))
    mask = set(json.loads(gzip.decompress((root/'github_assets/groom/hair_mask.json.gz').read_bytes()))['faces'])
    positions = {int(i):Vector(p) for i,p in source['vertices'].items()}
    faces = [f for f in source['faces'] if f['id'] in mask]
    indices = {old:i for i,old in enumerate(positions)}
    bvh = BVHTree.FromPolygons(list(positions.values()),
                              [[indices[v] for v in f['v']] for f in source['faces']],
                              all_triangles=False)
    areas,area = [],0.
    for face in faces:
        a,b,c = (positions[v] for v in face['v'])
        area += (b-a).cross(c-a).length/2.
        areas.append(area)
    rng = random.Random(382)
    nprng = np.random.default_rng(382)
    spacing = .0065
    roots,grid = [],defaultdict(list)
    for _ in range(130000):
        face = faces[bisect.bisect_left(areas,rng.random()*area)]
        a,b,c = (positions[v] for v in face['v'])
        u,v = math.sqrt(rng.random()),rng.random()
        weights = (1.-u,u*(1.-v),u*v)
        root = a*weights[0]+b*weights[1]+c*weights[2]
        part = .040+.13*(root.y+.070)
        if root.z>1.720 and -.105<root.y<.065 and abs(root.x-part)<.0035:
            continue
        cell = tuple(math.floor(v/spacing) for v in root)
        neighbors = (p for x in range(cell[0]-1,cell[0]+2)
                     for y in range(cell[1]-1,cell[1]+2)
                     for z in range(cell[2]-1,cell[2]+2)
                     for p in grid.get((x,y,z),()))
        if any((p-root).length_squared<spacing*spacing for p in neighbors):
            continue
        grid[cell].append(root)
        roots.append((root,face,weights))

    children,steps = 48,25
    t = np.linspace(0.,1.,steps,dtype=np.float32)
    points = np.empty((len(roots),children,steps,3),np.float32)
    radii = np.empty((len(roots),children,steps),np.float32)
    uvs = np.empty((len(roots),children,2),np.float32)
    for gi,(root,face,weights) in enumerate(roots):
        normal = Vector(face['normal']).normalized()
        ellipsoid = Vector((root.x/.095**2,(root.y-.012)/.115**2,(root.z-1.682)/.118**2)).normalized()
        if normal.dot(ellipsoid)<0:
            normal.negate()
        normal = (normal*.35+ellipsoid*.65).normalized()
        part = .040+.13*(root.y+.070)
        in_part = root.z>1.720 and -.105<root.y<.065
        direction = Vector((-.85,.30,.05))
        if root.x>part and root.y<.035:
            direction = Vector((.25,.65,-.30))
        elif root.y>.035:
            direction = Vector((0.,.65,-.50))
        side_weight = max(0., min(1., (abs(root.x)-.045)/.035))*max(0., min(1., (1.78-root.z)/.07))
        direction = direction.lerp(Vector((0., .85, -.4)), side_weight)
        tangent = (direction-normal*direction.dot(normal)).normalized()
        across = normal.cross(tangent).normalized()
        theta = rng.uniform(-.40,.40)
        if coherent:
            # Keep the broad flow, but vary neighboring curl planes. Purely
            # coherent directions made the compact curls read as rows of wire.
            flow = math.sin(root.x * math.tau / .045 + root.y * math.tau / .060)
            size_field = .5 + .5 * math.sin(root.x * math.tau / .055 - root.y * math.tau / .070)
            theta = .16 * flow + .70 * theta
        tangent = (tangent*math.cos(theta)+across*math.sin(theta)).normalized()
        across = normal.cross(tangent).normalized()
        curl_axis, curl_normal, curl_across = tangent, normal, across
        if coherent:
            # Reference ringlets lie along the head surface. A mostly tangent
            # axis turns their loops edge-on and makes the crown read as wire.
            clump = (.60 * math.sin(root.x * math.tau / .021 + root.y * math.tau / .027)
                     + .40 * math.sin(root.x * math.tau / .014 - root.y * math.tau / .019 + 1.7))
            tilt = 1.25 + .22 * clump
            curl_axis = (tangent*math.cos(tilt) + normal*math.sin(tilt)).normalized()
            curl_normal = (normal-curl_axis*normal.dot(curl_axis)).normalized()
            curl_across = curl_normal.cross(curl_axis).normalized()
        topness = min(1.,max(0.,(root.z-1.69)/.08))
        curl_radius = rng.uniform(.0045,.0065)*(.60+.40*topness)
        axial_length = rng.uniform(.012,.020)*(.50+.50*topness)
        curl_radius *= 1.-.68*side_weight
        axial_length *= 1.-.55*side_weight
        turns = rng.uniform(.85,1.65)*(1.-.30*side_weight)
        if coherent:
            curl_radius = (.0055 + .0015 * size_field) * (.60 + .40 * topness) * (1. - .68 * side_weight)
            # With the axis pointing mostly outward, keep pitch shallow so the
            # curl forms a low ringlet rather than a stack projecting off scalp.
            axial_length = (.0015 + .0015 * size_field) * (.50 + .50 * topness) * (1. - .55 * side_weight)
            turns = (1.05 + .15 * size_field) * (1. - .30 * side_weight)
        if in_part and abs(root.x-part)<.012:
            curl_radius *= .77
        phase_warp = t+rng.uniform(-.14,.14)*np.sin(math.pi*t)
        if coherent:
            phase_warp = t + .035 * flow * np.sin(math.pi*t)
        angle = turns*math.tau*phase_warp
        radius = curl_radius*(1.-rng.uniform(.05,.35)*t)
        if coherent:
            radius = curl_radius * (1. - .12 * t)
        height = radius*(1.-np.cos(angle))+.0006+.0005*np.sin(math.pi*t)
        side = radius*np.sin(angle)
        center = (np.asarray(root)[None,:]
                  +np.asarray(curl_normal)[None,:]*height[:,None]
                  +np.asarray(curl_across)[None,:]*side[:,None]
                  +np.asarray(curl_axis)[None,:]*(axial_length*t)[:,None])
        # Each bundle shares one curl. Fibers only vary within its cross section.
        # Their stable offsets retain clump thickness through the free tip.
        radial = (np.asarray(curl_normal)[None,:]*np.cos(angle)[:,None]
                  +np.asarray(curl_across)[None,:]*np.sin(angle)[:,None])
        spread_angle = nprng.uniform(0.,math.tau,children)
        spread_radius = np.sqrt(nprng.uniform(0.,1.,children))*rng.uniform(.0008,.00125)
        offset_radial = (np.cos(spread_angle)*spread_radius)[:,None,None]*radial[None,:,:]
        offset_axial = ((np.sin(spread_angle)*spread_radius)[:,None,None]
                        *np.asarray(curl_axis)[None,None,:])
        spread = (.82+.18*np.exp(-4.*t))[None,:,None]
        block = center[None,:,:]+(offset_radial+offset_axial)*spread
        wave_phase = nprng.uniform(0.,math.tau,children)
        wave_amplitude = nprng.uniform(.000008,.000065,children)
        wave = wave_amplitude[:,None]*np.sin(wave_phase[:,None]+t[None,:]*math.tau*2.)
        block += radial[None,:,:]*wave[:,:,None]
        for j,p in enumerate(center):
            near,n,_,_ = bvh.find_nearest(Vector(p))
            if near is not None:
                clearance = (Vector(p)-near).dot(n)
                if clearance<.0010:
                    block[:,j,:] += np.asarray(n)*(.0010-clearance)
        for k in range(children):
            near,n,_,_ = bvh.find_nearest(Vector(block[k,0]))
            if near is not None:
                block[k,0] = near+n*.00006
        if in_part:
            edge = .040+.13*(block[:,:,1]+.070)
            if root.x<part:
                block[:,:,0] = np.minimum(block[:,:,0],edge-.0015)
            else:
                block[:,:,0] = np.maximum(block[:,:,0],edge+.0015)
        points[gi] = block
        radius0 = nprng.uniform(.000034,.000048,children)
        radii[gi] = radius0[:,None]*(1.-.58*t**2)[None,:]
        radii[gi,:,-1] = .000004
        uvs[gi] = np.asarray(weights)@np.asarray(face['uv'])

    # A compact undercoat covers the softened scan between the larger ringlets.
    # It uses the same roots and tangential flow, with shorter lower curls.
    base_children = 12
    base_points = np.empty((len(roots),base_children,steps,3),np.float32)
    base_radii = np.empty((len(roots),base_children,steps),np.float32)
    base_uvs = np.empty((len(roots),base_children,2),np.float32)
    for gi,(root,face,weights) in enumerate(roots):
        normal = Vector(face['normal']).normalized()
        outward = Vector((root.x/.095**2,(root.y-.012)/.115**2,(root.z-1.682)/.118**2)).normalized()
        if normal.dot(outward)<0:
            normal.negate()
        normal = (normal*.35+outward*.65).normalized()
        part = .040+.13*(root.y+.070)
        direction = Vector((-.85,.30,.05)) if root.x<part else Vector((.25,.65,-.30))
        if root.y>.035:
            direction = Vector((0.,.65,-.50))
        tangent = (direction-normal*direction.dot(normal)).normalized()
        across = normal.cross(tangent).normalized()
        angle = nprng.uniform(.8,1.4,base_children)[:,None]*math.tau*t[None,:]
        radius = nprng.uniform(.0007,.0015,base_children)[:,None]
        height = .00025+radius*(1.-np.cos(angle))
        side = radius*np.sin(angle)
        along = nprng.uniform(.007,.013,base_children)[:,None]*t[None,:]
        block = (np.asarray(root)[None,None,:]+np.asarray(normal)[None,None,:]*height[:,:,None]
                 +np.asarray(across)[None,None,:]*side[:,:,None]
                 +np.asarray(tangent)[None,None,:]*along[:,:,None])
        offsets = (nprng.uniform(-.0018,.0018,base_children)[:,None]*np.asarray(across)[None,:]
                   +nprng.uniform(-.0018,.0018,base_children)[:,None]*np.asarray(tangent)[None,:])
        block += offsets[:,None,:]
        for j,p in enumerate(block.mean(axis=0)):
            near,n,_,_ = bvh.find_nearest(Vector(p))
            if near is not None:
                clearance = (Vector(p)-near).dot(n)
                if clearance<.00035:
                    block[:,j,:] += np.asarray(n)*(.00035-clearance)
        for k in range(base_children):
            near,n,_,_ = bvh.find_nearest(Vector(block[k,0]))
            if near is not None:
                block[k,0] = near+n*.00005
        if root.z>1.720 and -.105<root.y<.065:
            edge = .040+.13*(block[:,:,1]+.070)
            if root.x<part:
                block[:,:,0] = np.minimum(block[:,:,0],edge-.0015)
            else:
                block[:,:,0] = np.maximum(block[:,:,0],edge+.0015)
        base_points[gi] = block
        base_radii[gi] = nprng.uniform(.000035,.000047,base_children)[:,None]*(1.-.72*t**2)[None,:]
        base_radii[gi,:,-1] = .000003
        base_uvs[gi] = np.asarray(weights)@np.asarray(face['uv'])
    points = np.concatenate((points,base_points),axis=1)
    radii = np.concatenate((radii,base_radii),axis=1)
    uvs = np.concatenate((uvs,base_uvs),axis=1)
    children += base_children
    # Stop the underlying scan from producing a broad plastic highlight.
    underlay = bpy.data.materials['V371_DARK_HAIR_UNDERLAY']
    for shader in underlay.node_tree.nodes:
        if shader.type=='BSDF_PRINCIPLED':
            shader.inputs['Roughness'].default_value = .94
            shader.inputs['Specular IOR Level'].default_value = .10

    visibility = {}
    for name in ('V370_CURL_GROOM','V371_CURL_GROOM','V373_CURL_GROOM','V375_CURL_GROOM','V376_CURL_GROOM','V382_CURL_GROOM','V386_CURL_GROOM','V389_CURL_GROOM','V448_CURL_GROOM','V449_CURL_GROOM') + (('V544_CURL_GROOM',) if coherent else ()):
        old = bpy.data.objects.get(name)
        if old:
            visibility[name] = {'render':old.hide_render,'viewport':old.hide_get()}
            old.hide_render = True
            old.hide_set(True)
    (out/'previous_visibility_b.json').write_text(json.dumps(visibility,indent=2))
    curves = bpy.data.hair_curves.new(version + '_LOOSE_CURL_STRANDS')
    curves.add_curves([steps]*(len(roots)*children))
    curves.set_types(type='CATMULL_ROM')
    curves.position_data.foreach_set('vector',points.ravel())
    curves.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel())
    curves.attributes.new('surface_uv_coordinate','FLOAT2','CURVE').data.foreach_set('vector',uvs.ravel())
    curves.surface = body
    curves.surface_uv_map = body.data.uv_layers.active.name
    curves.surface_collision_distance = .0002
    mat = bpy.data.objects['V389_CURL_GROOM'].data.materials[0].copy()
    mat.name = version + '_BLACK_CURL_FIBER'
    shader = next(n for n in mat.node_tree.nodes if n.type=='BSDF_HAIR_PRINCIPLED')
    shader.inputs['Roughness'].default_value = .44
    shader.inputs['Random Roughness'].default_value = .12
    curves.materials.append(mat)
    obj = bpy.data.objects.new(version + '_CURL_GROOM',curves)
    bpy.context.scene.collection.objects.link(obj)
    bone = rig.pose.bones['DEF-Head']
    frame = rig.matrix_world@bone.matrix@Matrix.Translation((0,bone.bone.length,0))
    obj.parent,obj.parent_type,obj.parent_bone = rig,'BONE','DEF-Head'
    obj.matrix_parent_inverse = frame.inverted()
    obj.matrix_basis = Matrix.Identity(4)
    obj['guide_count'],obj['strand_count'] = len(roots),len(roots)*children
    obj['reference'] = 'character_an_front_v1.png'
    curves.update_tag()
    bpy.context.view_layer.update()
    report = {'guides':len(roots),'strands':len(roots)*children,'points':len(curves.points),
              'root_spacing_m':spacing,'build_seconds':time.monotonic()-started,
              'rig_drivers':len(rig.animation_data.drivers)}
    (out/'groom_report_b.json').write_text(json.dumps(report,indent=2))

    report['points_per_strand'] = steps
    report['coherent_flow'] = coherent
    report['local_direction_variation_radians'] = .28 if coherent else .40
    if coherent:
        report['curl_axis_tilt_radians'] = [1.03, 1.47]
        report['top_curl_pitch_m'] = [.0015, .003]
    report['version'] = version
    (out/'groom-report.json').write_text(json.dumps(report,indent=2))
    return report
