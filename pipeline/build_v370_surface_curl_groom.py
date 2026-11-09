"""Add a compact, clumped strand groom to the actual V369 scalp.

Run through the existing Blender MCP session. The preceding V369 .blend is
preserved. Curves follow DEF-Head; body topology and rig drivers are unchanged.
"""
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

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v370_curl_groom'
BODY = 'V357_TRIPO_CHARACTER_BODY_BOUND'
RIG = 'V357_CLOUDRIG_CONTROLS'


def material(name, hair=False, melanin=.91, roughness=.40):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    if hair:
        shader = nodes.new('ShaderNodeBsdfHairPrincipled')
        shader.parametrization = 'MELANIN'
        shader.inputs['Melanin'].default_value = melanin
        shader.inputs['Melanin Redness'].default_value = 0.10
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Radial Roughness'].default_value = roughness
        shader.inputs['IOR'].default_value = 1.55
        shader.inputs['Random Color'].default_value = 0.035
        shader.inputs['Random Roughness'].default_value = 0.12
    else:
        shader = nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Base Color'].default_value = (.0019, .0013, .0010, 1)
        shader.inputs['Roughness'].default_value = .78
        shader.inputs['Specular IOR Level'].default_value = .12
    mat.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
    mat.diffuse_color = (.006, .004, .003, 1)
    return mat


def main(version=370, target_guides=2100, children=26, melanin=.91, roughness=.40,
         radius_range=(.0019, .0034), clump_width=(.00040, .00085)):
    global OUT
    OUT = ROOT / f'production_v{version}_curl_groom'
    prefix = f'V{version}'
    started = time.monotonic()
    OUT.mkdir(exist_ok=True)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    head = rig.pose.bones['Head']
    for prop in ('Blink.L', 'Blink.R', 'JawOpen', 'GazeHorizontal', 'GazeVertical'):
        head[prop] = 0.
    rig.update_tag()
    bpy.context.view_layer.update()
    driver_count = len(rig.animation_data.drivers)
    assert driver_count == 1957, driver_count
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix+'_CURL_'):
            bpy.data.objects.remove(obj, do_unlink=True)
    data = json.loads((OUT / 'scalp_surface.json').read_text())
    mask = set(json.loads((OUT / 'hair_mask.json').read_text())['faces'])
    positions = {int(k): Vector(v) for k, v in data['vertices'].items()}
    faces = [face for face in data['faces'] if face['id'] in mask]
    cap = material(prefix+'_DARK_HAIR_UNDERLAY')
    slot = next((i for i, m in enumerate(body.data.materials) if m == cap), None)
    if slot is None:
        body.data.materials.append(cap)
        slot = len(body.data.materials) - 1
    for face in faces:
        body.data.polygons[face['id']].material_index = slot

    keys = list(positions)
    index = {old: i for i, old in enumerate(keys)}
    bvh = BVHTree.FromPolygons([positions[k] for k in keys],
                              [[index[v] for v in f['v']] for f in data['faces']],
                              all_triangles=False)
    areas = []
    total = 0.
    for f in faces:
        a, b, c = (positions[i] for i in f['v'])
        total += (b-a).cross(c-a).length / 2
        areas.append(total)

    rng = random.Random(version)
    steps = 28
    t = np.linspace(0., 1., steps, dtype=np.float32)
    point_blocks = []
    radius_blocks = []
    root_uvs = []
    guide_count = 0
    strand_count = 0
    root_clearances = []
    guide_limits = []
    for guide in range(target_guides):
        f = faces[bisect.bisect_left(areas, rng.random() * total)]
        a, b, c = (positions[i] for i in f['v'])
        u = math.sqrt(rng.random()); v = rng.random()
        weights = (1-u, u*(1-v), u*v)
        root = a*weights[0]+b*weights[1]+c*weights[2]
        normal = Vector(f['normal']).normalized()
        ellipsoid = Vector((root.x/.095**2, (root.y-.012)/.115**2,
                            (root.z-1.682)/.118**2)).normalized()
        if normal.dot(ellipsoid) < 0:
            normal.negate()
        normal = (normal*.32+ellipsoid*.68).normalized()
        # Preserve the narrow side part shown in the approved character sheet.
        part_x = .040 + .13*(root.y+.070)
        in_part_zone = root.z > 1.720 and -.105 < root.y < .065
        if in_part_zone and abs(root.x-part_x) < .0023:
            continue
        direction = Vector((-.85, .30, .05))
        if root.x > part_x and root.y < .035:
            direction = Vector((.25, .65, -.30))
        elif root.y > .035:
            direction = Vector((0., .65, -.50))
        tangent = (direction-normal*direction.dot(normal)).normalized()
        across = normal.cross(tangent).normalized()
        if tangent.length < .9:
            tangent = normal.cross(Vector((0, 1, 0))).normalized()
            across = normal.cross(tangent).normalized()
        topness = max(0., min(1., (root.z-1.69)/.08))
        curl_radius = rng.uniform(*radius_range) * (.72+.28*topness)
        turns = rng.uniform(1.0, 1.65)
        lift = rng.uniform(.0030, .0070) * (.55+.45*topness)
        drift = rng.uniform(.0020, .0050)
        phase = rng.random()*math.tau
        if in_part_zone and abs(root.x-part_x) < .009:
            curl_radius *= .7
        guide_points = []
        for tj in t:
            angle = phase + math.tau*turns*float(tj)
            growth = min(1., float(tj)*7.)
            p = root + normal*(.00028+lift*float(tj)) + tangent*(drift*float(tj))
            p += tangent*curl_radius*growth*(math.cos(angle)-math.cos(phase))
            p += across*curl_radius*growth*(math.sin(angle)-math.sin(phase))
            near, n, _, _ = bvh.find_nearest(p)
            if near is not None:
                signed = (p-near).dot(n)
                if signed < .00028:
                    p += n*(.00028-signed)
            if in_part_zone and -.105 < p.y < .065:
                px = .040+.13*(p.y+.070)
                if root.x < part_x:
                    p.x = min(p.x, px-.0015)
                else:
                    p.x = max(p.x, px+.0015)
            guide_points.append(p)
        centerline = np.asarray(guide_points, dtype=np.float32)
        uv = np.asarray(f['uv'], dtype=np.float32)
        root_uv = sum(uv[i]*weights[i] for i in range(3))
        for child in range(children):
            angle = rng.random()*math.tau
            width = math.sqrt(rng.random())*rng.uniform(*clump_width)
            offset = tangent*(math.cos(angle)*width)+across*(math.sin(angle)*width)
            phase_jitter = rng.uniform(-.1, .1)
            spread = (1.-.42*t)[:, None]
            points = centerline + np.asarray(offset, dtype=np.float32)[None, :]*spread
            wave = np.sin(t*math.tau*turns+phase_jitter)*rng.uniform(.00001, .00008)
            points += wave[:, None]*np.asarray(across, dtype=np.float32)
            near, n, _, _ = bvh.find_nearest(Vector(points[0]))
            if near is not None:
                points[0] = np.asarray(near+n*.00008, dtype=np.float32)
                if child == 0:
                    root_clearances.append(.00008)
            rad = rng.uniform(.000025, .000045)
            radii = rad*(1.-.80*t**2)
            radii[-1] = .0000025
            point_blocks.append(points)
            radius_blocks.append(radii)
            root_uvs.append(root_uv)
            strand_count += 1
        guide_count += 1
        guide_limits.extend([p.z for p in (guide_points[0], guide_points[-1])])

    curves = bpy.data.hair_curves.new(prefix+'_CURL_STRANDS')
    curves.add_curves([steps]*strand_count)
    curves.set_types(type='CATMULL_ROM')
    coordinates = np.concatenate(point_blocks).astype(np.float32).ravel()
    radii = np.concatenate(radius_blocks).astype(np.float32)
    curves.position_data.foreach_set('vector', coordinates)
    radius_attr = curves.attributes.new('radius', 'FLOAT', 'POINT')
    radius_attr.data.foreach_set('value', radii)
    uv_attr = curves.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE')
    uv_attr.data.foreach_set('vector', np.asarray(root_uvs, dtype=np.float32).ravel())
    curves.surface = body
    curves.surface_uv_map = body.data.uv_layers.active.name
    curves.surface_collision_distance = .0002
    curves.materials.append(material(prefix+'_MELANIN_BLACK_HAIR', hair=True,
                                    melanin=melanin, roughness=roughness))
    obj = bpy.data.objects.new(prefix+'_CURL_GROOM', curves)
    bpy.context.scene.collection.objects.link(obj)
    bone = rig.pose.bones['DEF-Head']
    frame = rig.matrix_world @ bone.matrix @ Matrix.Translation((0, bone.bone.length, 0))
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = 'DEF-Head'
    obj.matrix_parent_inverse = frame.inverted()
    obj.matrix_basis = Matrix.Identity(4)
    obj['reference'] = 'head_expression_sheet_v2_face_refined.png'
    obj['guide_count'] = guide_count
    obj['strand_count'] = strand_count
    obj['root_radius_m'] = [.000025, .000045]
    curves.update_tag()
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 1
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.camera.data.ortho_scale = .37
    assert len(rig.animation_data.drivers) == driver_count
    report = {'source': data.get('source', 'V369'), 'guides': guide_count, 'strands': strand_count,
              'points': len(curves.points), 'masked_faces': len(faces),
              'scalp_area_m2': total, 'root_radius_m': [.000025, .000045],
              'rig_drivers': driver_count, 'build_seconds': time.monotonic()-started,
              'status': 'FIRST_GROOM_REQUIRES_VISUAL_REVIEW'}
    (OUT/'groom_report.json').write_text(json.dumps(report, indent=2))
    for name, loc in [('front', (0, -1.4, 1.66)),
                      ('threequarter', (.53, -1.25, 1.69))]:
        scene.camera.location = loc
        scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(OUT/f'v{version}_groom_{name}.png')
        bpy.ops.render.render(write_still=True)
    scene.camera.location = (0, -1.4, 1.66)
    scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'Character_An_surface_curl_groom_v{version}.blend'), compress=True)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
