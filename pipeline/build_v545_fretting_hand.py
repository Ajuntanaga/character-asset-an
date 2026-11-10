"""Fit the native left donor to the approved M3 fretting pose, on Actions."""
import json
import math
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from guitar_geometry import GuitarGeometry, load_authoritative_mapping

DIGITS = ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')
PAD_MIN_DOT = math.cos(math.radians(35.))
NAIL_MIN_DOT = math.cos(math.radians(60.))


def frame(bones, side):
    wrist = bones[f'DEF-Hand.{side}'].head_local
    along = (bones[f'DEF-Finger_Middle1.{side}'].head_local - wrist).normalized()
    across = bones[f'DEF-Finger_Index1.{side}'].head_local - bones[f'DEF-Finger_Pinky1.{side}'].head_local
    across = (across - along * across.dot(along)).normalized()
    return Matrix((across, along, across.cross(along))).transposed()


def tree_for(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices],
                                   [list(p.vertices) for p in mesh.polygons])
    finally:
        evaluated.to_mesh_clear()


def pad_trees_for(obj):
    """Keep each pad on its own distal skin, excluding nails and other digits."""
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        groups = {obj.vertex_groups[f'DEF-Finger_{d}3.R'].index: d for d in DIGITS}
        owners = {v.index: next((groups[g.group] for g in v.groups
                                if g.group in groups and g.weight > .95), None)
                  for v in mesh.vertices}
        faces = {d: [] for d in DIGITS}
        ids = {d: [] for d in DIGITS}
        for polygon in mesh.polygons:
            digit = owners[polygon.vertices[0]]
            if (polygon.material_index == 0 and digit is not None and
                    all(owners[i] == digit for i in polygon.vertices)):
                faces[digit].append(list(polygon.vertices))
                ids[digit].append(polygon.index)
        vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        assert all(faces.values()), 'Missing weighted distal skin region'
        return {d: (BVHTree.FromPolygons(vertices, faces[d]), ids[d]) for d in DIGITS}
    finally:
        evaluated.to_mesh_clear()


def sample_pad(trees, digit, matrix, pad):
    anchor = matrix @ pad[0]
    expected_normal = (matrix.to_3x3().inverted().transposed() @ pad[1]).normalized()
    tree, polygon_ids = trees[digit]
    point, normal, index, distance = tree.find_nearest(anchor, .004)
    assert point is not None, f'{digit} pad lost its persistent skin anchor'
    if normal.dot(expected_normal) < 0:
        normal.negate()
    return point, normal, polygon_ids[index], distance


def minimize(residual, initial, low, high, iterations=40):
    x = np.clip(initial, low, high)
    history = []
    for iteration in range(iterations):
        r = residual(x)
        columns = []
        for j in range(len(x)):
            step = .0001 if j < 3 else .002
            v = x.copy(); v[j] += step
            columns.append((residual(v) - r) / step)
        jac = np.array(columns).T
        # Solve the bounded quadratic step itself: clipping an unconstrained
        # solution can eliminate descent when several joints hit their limits.
        trust = np.r_[[.012] * 3, [.18] * (len(x) - 3)]
        scaled = jac * trust
        hessian = scaled.T @ scaled + np.eye(len(x)) * 1e-7
        gradient = scaled.T @ r
        lower = np.maximum(-1., (low - x) / trust)
        upper = np.minimum(1., (high - x) / trust)
        step = np.zeros(len(x))
        for _ in range(160):
            previous = step.copy()
            for j in range(len(x)):
                step[j] = np.clip(step[j] - (hessian[j] @ step + gradient[j]) /
                                  hessian[j, j], lower[j], upper[j])
            if np.max(np.abs(step - previous)) < 1e-6:
                break
        delta = step * trust
        best = (float(r @ r), x.copy())
        for rate in (1., .5, .2, .05, .01):
            v = np.clip(x + rate * delta, low, high)
            rr = residual(v)
            if float(rr @ rr) < best[0]:
                best = (float(rr @ rr), v)
        history.append(best[0])
        if np.linalg.norm(best[1] - x) < 1e-5:
            break
        x = best[1]
    return x, history


def build(out, thumb_support='fixed', relaxed_contact_dips=False, spread_trial=False, wrist_extension=False):
    assert thumb_support in ('fixed', 'sliding_rear')
    assert Path(bpy.data.filepath).name == 'current-v544.blend'
    scene = bpy.context.scene
    main = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    right = bpy.data.objects['V528_NATIVE_RIG.R']
    pick = bpy.data.objects['V361_NYLON_PICK']
    pick_before = pick.matrix_world.copy()
    assert len(main.animation_data.drivers) == 1957
    donor_path = Path('scenes/native-hand-v522.blend').resolve()
    with bpy.data.libraries.load(str(donor_path), link=False) as (_, data):
        data.objects = ['V522_NATIVE_HAND', 'V522_NATIVE_RIG']
    for obj in data.objects:
        scene.collection.objects.link(obj)
    hand = next(o for o in data.objects if o.type == 'MESH')
    rig = next(o for o in data.objects if o.type == 'ARMATURE')
    hand.name = 'V545_NATIVE_HAND.L'; rig.name = 'V545_NATIVE_RIG.L'
    hand.parent = rig; hand.matrix_parent_inverse = Matrix.Identity(4)
    hand.matrix_basis = Matrix.Identity(4)
    rig.matrix_world = Matrix.Identity(4)
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    source = rig.data.bones
    sf = frame(source, 'R'); tf = frame(main.data.bones, 'L')
    wrist_source = source['DEF-Hand.R'].head_local.copy()
    source_palm = source['DEF-Finger_Middle1.R'].head_local - wrist_source
    right_palm = (right.matrix_world.to_3x3() @ source_palm).length
    posed = main.matrix_world @ main.pose.bones['DEF-Hand.L'].matrix @ main.data.bones['DEF-Hand.L'].matrix_local.inverted()
    initial_linear = posed.to_quaternion().to_matrix() @ tf @ sf.inverted()
    # Match the existing donor's palm length, without copying the enlarged old hand.
    scale = right_palm / (initial_linear @ source_palm).length
    initial_linear = initial_linear * scale
    old = bpy.data.objects['V357_ANATOMICAL_HAND.L']
    bm = bmesh.new(); bm.from_mesh(hand.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                          dist=1e-6, plane_co=wrist_source - sf.col[1] * .012,
                          plane_no=sf.col[1], clear_inner=True, clear_outer=False)
    bm.to_mesh(hand.data); bm.free()
    indices = [p.material_index for p in hand.data.polygons]
    hand.data.materials.clear()
    for material in old.data.materials:
        hand.data.materials.append(material)
    for polygon, index in zip(hand.data.polygons, indices):
        polygon.material_index = 1 if index in (5, 6) else 0
    assert any(p.material_index == 1 for p in hand.data.polygons), 'Donor nails lost'
    subdivisions = [(m, m.levels) for m in hand.modifiers if m.type == 'SUBSURF']
    for modifier, _ in subdivisions:
        modifier.levels = 1
    bpy.context.view_layer.update()
    # Identify each pad opposite its nail, including the rounded distal pulp.
    rest_trees = pad_trees_for(hand)
    nail_vertices = {i for p in hand.data.polygons if p.material_index == 1 for i in p.vertices}
    pads = {}; nail_directions = {}; axes = {}; spreads = {}
    for digit in DIGITS:
        name = f'DEF-Finger_{digit}3.R'
        bone = source[name]; group = hand.vertex_groups[name].index
        ids = [v.index for v in hand.data.vertices if v.index in nail_vertices and
               any(g.group == group and g.weight > .6 for g in v.groups)]
        assert ids, f'Missing {digit} nail reference'
        nail = sum((hand.data.vertices[i].co for i in ids), Vector()) / len(ids)
        along = (bone.tail_local - bone.head_local).normalized()
        radial = bone.head_local - nail
        radial = (radial - along * radial.dot(along)).normalized()
        direction = (radial * .8 + along * .6).normalized()
        origin = bone.head_local.lerp(bone.tail_local, .6)
        point, normal, _, _ = rest_trees[digit][0].ray_cast(origin, direction, .04)
        assert point is not None, f'Missing {digit} pad surface'
        if normal.dot(direction) < 0:
            normal.negate()
        pads[digit] = (bone.matrix_local.inverted() @ point,
                       bone.matrix_local.to_3x3().inverted() @ normal)
        # Keep the dorsal nail direction independent of the ray-hit normal.
        # A rounded/lateral surface can face the string with the nail sideways.
        nail_directions[digit] = bone.matrix_local.to_3x3().inverted() @ -radial
        for j in (1, 2, 3):
            b = source[f'DEF-Finger_{digit}{j}.R']
            direction = (b.tail_local - b.head_local).normalized()
            axis = sf.col[2].cross(direction).normalized()
            if axis.cross(direction).dot(radial) < 0:
                axis.negate()
            axes[(digit, j)] = b.matrix_local.to_3x3().inverted() @ axis
            spreads[(digit, j)] = b.matrix_local.to_3x3().inverted() @ sf.col[2]
    guitar = bpy.data.objects['V206_GUITAR_ROOT'].matrix_world.copy()
    guitar_inv = guitar.inverted()
    normal = (guitar.to_3x3() @ Vector((0, 0, 1))).normalized()
    mapping = load_authoritative_mapping(); geometry = GuitarGeometry.from_mapping(mapping)
    targets = {}; target_meta = {}
    for item in mapping['visible_pose_targets']:
        digit = item['finger'].title()
        px, py, _ = geometry.local_pad_from_neutral(item['string'], item['fret'])
        string = bpy.data.objects['V206_STRING_' + item['string']]
        points = [guitar_inv @ string.matrix_world @ Vector(p.co[:3]) for p in string.data.splines[0].points]
        x = .260 + px
        a, b = next((a, b) for a, b in zip(points, points[1:]) if min(a.x, b.x) <= x <= max(a.x, b.x))
        z = a.z + (b.z - a.z) * (x - a.x) / (b.x - a.x) + string.data.bevel_depth
        if not item['contact']:
            z += .010
        targets[digit] = guitar @ Vector((x, py, z))
        target_meta[digit] = dict(item, world=list(targets[digit]))
    center_x = sum((guitar_inv @ p).x for p in targets.values()) / 4
    neck_tree = tree_for(bpy.data.objects['V206_NECK'])
    origin = guitar @ Vector((center_x, 0, -.09))
    thumb_target, _, _, _ = neck_tree.ray_cast(origin, normal, .15)
    assert thumb_target is not None, 'Rear neck target missing'
    targets['Thumb'] = thumb_target - normal * .0003
    target_meta['Thumb'] = {'role': 'rear-neck support', 'world': list(targets['Thumb'])}
    # The reference fixes the thumb's support surface, not its tangent position.
    # Preserve all finger/string assignments while allowing natural rear-neck sliding.
    support_x = (min((guitar_inv @ p).x for d, p in targets.items() if d != 'Thumb') - .04,
                 max((guitar_inv @ p).x for d, p in targets.items() if d != 'Thumb') + .04)
    def thumb_goal(point):
        if thumb_support == 'fixed':
            return targets['Thumb'], normal
        local = guitar_inv @ point
        x = max(support_x[0], min(support_x[1], local.x))
        y = max(-.020, min(.020, local.y))
        hit, outward, _, _ = neck_tree.ray_cast(guitar @ Vector((x, y, -.09)), normal, .15)
        assert hit is not None and outward.dot(normal) < -.5, 'Rear support surface missing'
        return hit + outward * .0003, -outward
    # Palm surface and wrist interior must clear the actual neck, not just
    # satisfy fingertip targets. These vertices are rigidly weighted to Hand.
    palm_group = hand.vertex_groups['DEF-Hand.R'].index
    palm_samples = [v.co.copy() for v in hand.data.vertices
                    if any(g.group == palm_group and g.weight > .98 for g in v.groups)]
    assert palm_samples, 'No rigid palm collision samples'
    # Include the cut wrist interior: surface-only samples can surround a neck
    # while leaving an undetected intersection through the open boundary.
    wrist_samples = [wrist_source + sf.col[1] * offset for offset in (-.012, 0., .012)]
    def neck_clearance(point):
        near, outward, _, _ = neck_tree.find_nearest(point)
        assert near is not None
        return (point - near).dot(outward)

    rest = {b.name: b.matrix_local.copy() for b in source}
    relative = {b.name: rest[b.parent.name].inverted() @ rest[b.name] if b.parent else rest[b.name] for b in source}
    # Variables: guitar-local wrist, world rotation, four flex/flex/flex/splay sets,
    # then thumb flex/opposition/flex/flex/axial roll. The donor is already a
    # left hand despite its .R bone names. Native joint lengths never change.
    prior = np.r_[[center_x, .125, -.060], [0., 0., 0.],
                  np.radians([45, 75, 40, 0] * 4 + [20, 20, 10, 5, 0])]
    low = np.r_[[center_x - .09, .045, -.125], [-1.5] * 3,
                np.radians([0, 10, 12, -25] * 4 + [-45, -75, -10, -10, -90])]
    high = np.r_[[center_x + .09, .185, .025], [1.5] * 3,
                 np.radians([95, 105, 80, 25] * 4 + [60, 75, 20, 15, 90])]

    def matrices(values):
        linear = Euler(tuple(values[3:6]), 'XYZ').to_matrix() @ initial_linear
        world = linear.to_4x4()
        world.translation = guitar @ Vector(values[:3]) - linear @ wrist_source
        pose = {'DEF-Hand.R': rest['DEF-Hand.R']}
        rotations = {}
        for index, digit in enumerate(DIGITS):
            offset = 6 + index * 4
            flex = values[offset:offset + 3] if digit != 'Thumb' else values[[22, 24, 25]]
            splay = values[offset + 3] if digit != 'Thumb' else values[23]
            for j in (1, 2, 3):
                name = f'DEF-Finger_{digit}{j}.R'
                q = Quaternion(axes[(digit, j)], float(flex[j - 1]))
                if j == 1:
                    q = Quaternion(spreads[(digit, j)], float(splay)) @ q
                    if digit == 'Thumb':
                        # CMC opposition includes axial rotation. Without it,
                        # the solver folds MCP/IP to turn the pad toward the neck.
                        q = q @ Quaternion((0., 1., 0.), float(values[26]))
                rotations[name] = q
                pose[name] = pose[source[name].parent.name] @ relative[name] @ q.to_matrix().to_4x4()
        return world, pose, rotations

    def contacts(values, evaluated=False):
        world, pose, rotations = matrices(values)
        if evaluated:
            rig.matrix_world = world
            for name, q in rotations.items():
                b = rig.pose.bones[name]; b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = q
            bpy.context.view_layer.update()
            trees = pad_trees_for(hand)
        result = {}
        for digit in DIGITS:
            name = f'DEF-Finger_{digit}3.R'
            matrix = world @ pose[name]
            if evaluated:
                matrix = rig.matrix_world @ rig.pose.bones[name].matrix
                point, n, _, _ = sample_pad(trees, digit, matrix, pads[digit])
            else:
                point = matrix @ pads[digit][0]
                n = (matrix.to_3x3().inverted().transposed() @ pads[digit][1]).normalized()
            nail_direction = (matrix.to_3x3() @ nail_directions[digit]).normalized()
            result[digit] = (point, n, nail_direction)
        return result, world, pose

    def residual(values, evaluated=False):
        points, world, pose = contacts(values, evaluated)
        r = []
        for digit, (point, n, nail_direction) in points.items():
            target, desired = thumb_goal(point) if digit == 'Thumb' else (targets[digit], -normal)
            r.extend(point - target)
            r.extend((n - desired) * .002)
            # Orientation is an explicit acceptance condition below. The
            # high-weight cone penalties guide the fit without demanding a
            # perfectly flat pad/nail on the rounded fingertip.
            r.append(max(0., PAD_MIN_DOT - n.dot(desired)) * .08)
            r.append(max(0., NAIL_MIN_DOT - nail_direction.dot(-desired)) * .08)
        # Keep non-thumb knuckles and shafts on the front/edge of the fretboard.
        for digit in DIGITS[:4]:
            for j in (1, 2, 3):
                name = f'DEF-Finger_{digit}{j}.R'
                p = guitar_inv @ world @ pose[name] @ Vector((0, source[name].length * .5, 0))
                edge = max(0., min(1., (.045 - abs(p.y)) / .008))
                r.append(min(0., p.z - .031) * edge)
        # Keep a fixed residual size and balance dense palm samples against
        # five contact constraints. Interior wrist samples use a small radius.
        weight = math.sqrt(8. / len(palm_samples))
        r.extend(min(0., neck_clearance(world @ p) - .001) * weight
                 for p in palm_samples)
        r.extend(min(0., neck_clearance(world @ p) - .008) * 2.
                 for p in wrist_samples)
        for j in (1, 2, 3):
            name = f'DEF-Finger_Thumb{j}.R'
            point = world @ pose[name] @ Vector((0, source[name].length * .5, 0))
            r.append(min(0., neck_clearance(point) - .004))
            # The approved thumb supports the rear of the neck; it must not
            # curl over the fretboard toward the fretting camera.
            r.append(max(0., (guitar_inv @ point).z + .006))
        r.extend((values[:3] - prior[:3]) * .025)
        r.extend((values[3:6] - prior[3:6]) * .00035)
        for index in range(4):
            offset = 6 + index * 4
            r.extend((values[offset:offset + 3] - prior[offset:offset + 3]) * .0015)
            r.append((values[offset + 3] - prior[offset + 3]) * .0005)
            # Retain a rounded fingertip rather than extending every DIP to
            # zero just to minimize the five contact distances.
            r.append((values[offset + 2] - .55 * values[offset + 1]) * .0025)
        r.extend((values[[22, 23, 26]] - prior[[22, 23, 26]]) * .0004)
        r.extend((values[24:26] - prior[24:26]) * .003)
        return np.array(r)

    contacts(prior, True)
    expected_world, expected_pose, _ = matrices(prior)
    joint_error = max((expected_world @ expected_pose[b.name].translation -
                       rig.matrix_world @ b.head).length for b in rig.pose.bones)
    assert joint_error < 1e-5, f'Analytic/evaluated joint mismatch: {joint_error}'
    print('Fitting native left hand: analytic joints', flush=True)
    # Earlier axial-roll seeds all converged to the same hooked pose. Solve
    # once with the revised pad frame and extended thumb joint limits.
    initial = prior
    if thumb_support == 'sliding_rear':
        seed = json.loads((Path(__file__).resolve().parents[1] / 'github_assets/fretting-seed-v599.json').read_text())
        initial = np.asarray(seed['values'], dtype=float)
        assert initial.shape == prior.shape and np.all(np.isfinite(initial))
    if relaxed_contact_dips:
        # Isolate the forced curl constraint on the two unresolved contact digits.
        low[[8, 16]] = 0.
        seed = json.loads((Path(__file__).resolve().parents[1] / 'github_assets/fretting-seed-v602.json').read_text())
        initial = np.asarray(seed['values'], dtype=float)
        assert initial.shape == prior.shape and np.all(np.isfinite(initial))
    if spread_trial:
        # V602 stops at opposite index/ring spread limits with 8-10 mm gaps.
        # Isolate that constraint; preserve joint lengths and all acceptance gates.
        assert relaxed_contact_dips and thumb_support == 'sliding_rear'
        low[[9, 17]] = math.radians(-35.)
        high[[9, 17]] = math.radians(35.)
        seed = json.loads((Path(__file__).resolve().parents[1] / 'github_assets/fretting-seed-v612.json').read_text())
        initial = np.asarray(seed['values'], dtype=float)
        assert initial.shape == prior.shape and np.all(np.isfinite(initial))
    values, coarse_history = minimize(residual, initial, low, high, 90)
    print(f'Coarse fit loss: {coarse_history[-1]}; refining evaluated skin', flush=True)
    values, surface_history = minimize(lambda v: residual(v, True), values, low, high, 24)
    print(f'Surface fit loss: {surface_history[-1]}; attaching to main arm', flush=True)
    points, desired_world, pose = contacts(values, True)
    desired_wrist = desired_world @ wrist_source
    # Move the real arm control to the solved wrist, allowing its reach constraints
    # to evaluate; preserve full affine donor placement in the bone-parent inverse.
    control = main.pose.bones['IK-Hand.L']
    for _ in range(8):
        actual = main.matrix_world @ main.pose.bones['DEF-Hand.L'].head
        error = desired_wrist - actual
        if error.length < .0001:
            break
        m = control.matrix.copy(); m.translation += main.matrix_world.to_3x3().inverted() @ error
        control.matrix = m; bpy.context.view_layer.update()
    actual_wrist = main.matrix_world @ main.pose.bones['DEF-Hand.L'].head
    wrist_error = (actual_wrist - desired_wrist).length
    assert wrist_error < .002, f'Arm cannot reach donor wrist: {wrist_error}'
    rig.parent = main; rig.parent_type = 'BONE'; rig.parent_bone = 'DEF-Hand.L'
    rig.matrix_parent_inverse = Matrix.Identity(4)
    rig.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    parent_frame = rig.matrix_world.copy()
    rig.matrix_parent_inverse = parent_frame.inverted() @ desired_world
    bpy.context.view_layer.update()
    attachment_error = max(abs(rig.matrix_world[i][j] - desired_world[i][j])
                           for i in range(4) for j in range(4))
    assert attachment_error < 1e-5, f'Donor attachment changed placement: {attachment_error}'
    # Expose flexion and MCP spread through the existing character controls.
    for index, digit in enumerate(DIGITS[:4]):
        for j in (1, 2, 3):
            b = rig.pose.bones[f'DEF-Finger_{digit}{j}.R']
            control_bone = main.pose.bones[f'FK-Finger_{digit}{j}.L']
            control_bone.rotation_euler.x = float(values[6 + index * 4 + j - 1])
            control_bone.rotation_euler.z = float(values[9 + index * 4]) if j == 1 else 0.
            a = axes[(digit, j)]; z = spreads[(digit, j)]
            cross = z.cross(a); dot = z.dot(a)
            expressions = [f'cos(s/2)*cos(f/2)-({dot})*sin(s/2)*sin(f/2)']
            expressions += [f'({a[k]})*cos(s/2)*sin(f/2)+({z[k]})*sin(s/2)*cos(f/2)+({cross[k]})*sin(s/2)*sin(f/2)' for k in range(3)]
            for component, expression in enumerate(expressions):
                driver = b.driver_add('rotation_quaternion', component).driver
                for var_name, axis_index in [('f', 0), ('s', 2)]:
                    variable = driver.variables.new(); variable.name = var_name; variable.type = 'SINGLE_PROP'
                    variable.targets[0].id = main
                    variable.targets[0].data_path = f'pose.bones["{control_bone.name}"].rotation_euler[{axis_index}]'
                driver.expression = expression
    wrist_report = None
    if wrist_extension:
        from build_v618_wrist_extension import extend_wrist
        wrist_report = extend_wrist(hand, rig, main, 'L')
    old.hide_render = True; old.hide_set(True)
    for modifier, level in subdivisions:
        modifier.levels = level
    main.update_tag(); bpy.context.view_layer.update()
    # Check final evaluated skin after parenting, controls and full subdivision.
    final_trees = pad_trees_for(hand)
    final = {}
    for digit in DIGITS:
        bone = rig.pose.bones[f'DEF-Finger_{digit}3.R']
        matrix = rig.matrix_world @ bone.matrix
        point, n, polygon, anchor_distance = sample_pad(final_trees, digit, matrix, pads[digit])
        target, desired = thumb_goal(point) if digit == 'Thumb' else (targets[digit], -normal)
        if digit == 'Thumb':
            target_meta['Thumb'].update(world=list(target), support_mode=thumb_support)
        nail_direction = (matrix.to_3x3() @ nail_directions[digit]).normalized()
        final[digit] = {'pad_world': list(point), 'target_world': list(target),
                        'distance_m': (point - target).length, 'normal': list(n),
                        'pad_alignment': n.dot(desired),
                        'nail_alignment': nail_direction.dot(-desired),
                        'surface_region': f'DEF-Finger_{digit}3.R',
                        'evaluated_polygon_index': polygon,
                        'anchor_distance_m': anchor_distance}
    actual_palm = (rig.matrix_world.to_3x3() @ source_palm).length
    pick_error = max(abs(pick.matrix_world[i][j] - pick_before[i][j]) for i in range(4) for j in range(4))
    assert pick_error < 1e-5 and len(main.animation_data.drivers) == 1957
    palm_clearance = min(neck_clearance(rig.matrix_world @ p) for p in palm_samples)
    wrist_clearance = min(neck_clearance(rig.matrix_world @ p) - .008 for p in wrist_samples)
    orientation_ok = all(c['pad_alignment'] >= PAD_MIN_DOT and
                         c['nail_alignment'] >= NAIL_MIN_DOT for c in final.values())
    contact_ok = (max(c['distance_m'] for c in final.values()) < .003 and
                  min(palm_clearance, wrist_clearance) >= -.0005)
    fit_status = ('TRIAL_REQUIRES_VISUAL_AND_DEFORMATION_REVIEW' if contact_ok and orientation_ok
                  else 'REJECTED_CONTACT_OR_ORIENTATION_FIT')
    report = {'status': fit_status, 'main_drivers': 1957,
              'wrist_extension': wrist_report,
              'revision': 'V612' if spread_trial else 'V602' if relaxed_contact_dips else ('V599' if thumb_support == 'sliding_rear' else 'V545'),
              'relaxed_index_ring_dip_minimum': relaxed_contact_dips,
              'index_ring_spread_limit_degrees': 35 if spread_trial else 25,
              'thumb_support_mode': thumb_support,
              'thumb_support_x_bounds_m': list(support_x),
              'thumb_support_y_bounds_m': [-.020, .020],
              'native_drivers': len(rig.animation_data.drivers), 'targets': target_meta,
              'palm_neck_clearance_m': palm_clearance,
              'wrist_neck_clearance_m': wrist_clearance,
              'palm_collision_samples': len(palm_samples),
              'contacts': final, 'left_palm_m': actual_palm, 'right_palm_m': right_palm,
              'wrist_anchor_error_m': wrist_error, 'pick_matrix_error': pick_error,
              'values': values.tolist(), 'coarse_loss': coarse_history, 'surface_loss': surface_history,
              'thumb_axial_roll_degrees': math.degrees(values[26]),
              'thumb_distal_flexion_degrees': np.degrees(values[24:26]).tolist(),
              'orientation_limits': {'pad_min_dot': PAD_MIN_DOT, 'nail_min_dot': NAIL_MIN_DOT},
              'pad_sampling': 'nearest own distal skin to persistent pad; weight > 0.95; radius 4mm',
              'contact_ok': contact_ok, 'orientation_ok': orientation_ok,
              'nail_polygons': sum(p.material_index == 1 for p in hand.data.polygons)}
    (out / 'hand-fit-report.json').write_text(json.dumps(report, indent=2))
    # Appending retains a weak origin-library record even with all IDs local.
    assert not any(item.library for item in bpy.data.user_map()), 'Linked donor dependency'
    for library in list(bpy.data.libraries):
        bpy.data.libraries.remove(library)
    bpy.ops.wm.save_as_mainfile(filepath=str((out / 'Character_An_fretting_hand_TRIAL_v545.blend').resolve()))
    print(json.dumps(report), flush=True)
    return report
