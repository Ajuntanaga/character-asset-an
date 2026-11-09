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


def build(out):
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
    rest_tree = tree_for(hand)
    nail_vertices = {i for p in hand.data.polygons if p.material_index == 1 for i in p.vertices}
    pads = {}; radials = {}; axes = {}; spreads = {}
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
        point, normal, _, _ = rest_tree.ray_cast(origin, direction, .04)
        assert point is not None, f'Missing {digit} pad surface'
        if normal.dot(direction) < 0:
            normal.negate()
        pads[digit] = (bone.matrix_local.inverted() @ point,
                       bone.matrix_local.to_3x3().inverted() @ normal)
        radials[digit] = bone.matrix_local.to_3x3().inverted() @ direction
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
    # then thumb flex/opposition/flex/flex. Native joint lengths never change.
    prior = np.r_[[center_x, .125, -.060], [0., 0., 0.],
                  np.radians([45, 75, 40, 0] * 4 + [20, 20, 30, 15])]
    low = np.r_[[center_x - .09, .045, -.125], [-1.5] * 3,
                np.radians([0, 10, 0, -25] * 4 + [-45, -60, -10, -10])]
    high = np.r_[[center_x + .09, .185, .025], [1.5] * 3,
                 np.radians([95, 105, 80, 25] * 4 + [60, 60, 60, 55])]

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
            tree = tree_for(hand)
        result = {}
        for digit in DIGITS:
            name = f'DEF-Finger_{digit}3.R'
            matrix = world @ pose[name]
            if evaluated:
                matrix = rig.matrix_world @ rig.pose.bones[name].matrix
                direction = (matrix.to_3x3() @ radials[digit]).normalized()
                center = matrix @ Vector((0, source[name].length * .6, 0))
                point, n, _, _ = tree.ray_cast(center, direction, .035)
                if point is None:
                    raise RuntimeError(f'No evaluated {digit} pad')
                if n.dot(direction) < 0:
                    n.negate()
            else:
                point = matrix @ pads[digit][0]
                n = (matrix.to_3x3().inverted().transposed() @ pads[digit][1]).normalized()
            result[digit] = (point, n)
        return result, world, pose

    def residual(values, evaluated=False):
        points, world, pose = contacts(values, evaluated)
        r = []
        for digit, (point, n) in points.items():
            r.extend(point - targets[digit])
            desired = normal if digit == 'Thumb' else -normal
            r.extend((n - desired) * .003)
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
        r.extend((values[:3] - prior[:3]) * .025)
        r.extend((values[3:] - prior[3:]) * .00035)
        return np.array(r)

    contacts(prior, True)
    expected_world, expected_pose, _ = matrices(prior)
    joint_error = max((expected_world @ expected_pose[b.name].translation -
                       rig.matrix_world @ b.head).length for b in rig.pose.bones)
    assert joint_error < 1e-5, f'Analytic/evaluated joint mismatch: {joint_error}'
    print('Fitting native left hand: analytic joints', flush=True)
    values, coarse_history = minimize(residual, prior, low, high, 100)
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
    old.hide_render = True; old.hide_set(True)
    for modifier, level in subdivisions:
        modifier.levels = level
    main.update_tag(); bpy.context.view_layer.update()
    # Check final evaluated skin after parenting, controls and full subdivision.
    final_tree = tree_for(hand)
    final = {}
    for digit in DIGITS:
        bone = rig.pose.bones[f'DEF-Finger_{digit}3.R']
        matrix = rig.matrix_world @ bone.matrix
        direction = (matrix.to_3x3() @ radials[digit]).normalized()
        point, n, _, _ = final_tree.ray_cast(matrix @ Vector((0, bone.bone.length * .6, 0)), direction, .035)
        assert point is not None
        final[digit] = {'pad_world': list(point), 'target_world': list(targets[digit]),
                        'distance_m': (point - targets[digit]).length, 'normal': list(n)}
    actual_palm = (rig.matrix_world.to_3x3() @ source_palm).length
    pick_error = max(abs(pick.matrix_world[i][j] - pick_before[i][j]) for i in range(4) for j in range(4))
    assert pick_error < 1e-5 and len(main.animation_data.drivers) == 1957
    palm_clearance = min(neck_clearance(rig.matrix_world @ p) for p in palm_samples)
    wrist_clearance = min(neck_clearance(rig.matrix_world @ p) - .008 for p in wrist_samples)
    fit_status = ('TRIAL_REQUIRES_VISUAL_AND_DEFORMATION_REVIEW' if
                  max(c['distance_m'] for c in final.values()) < .003 and
                  min(palm_clearance, wrist_clearance) >= -.0005 else
                  'REJECTED_CONTACT_FIT')
    report = {'status': fit_status, 'main_drivers': 1957,
              'native_drivers': len(rig.animation_data.drivers), 'targets': target_meta,
              'palm_neck_clearance_m': palm_clearance,
              'wrist_neck_clearance_m': wrist_clearance,
              'palm_collision_samples': len(palm_samples),
              'contacts': final, 'left_palm_m': actual_palm, 'right_palm_m': right_palm,
              'wrist_anchor_error_m': wrist_error, 'pick_matrix_error': pick_error,
              'values': values.tolist(), 'coarse_loss': coarse_history, 'surface_loss': surface_history,
              'nail_polygons': sum(p.material_index == 1 for p in hand.data.polygons)}
    (out / 'hand-fit-report.json').write_text(json.dumps(report, indent=2))
    # Appending retains a weak origin-library record even with all IDs local.
    assert not any(item.library for item in bpy.data.user_map()), 'Linked donor dependency'
    for library in list(bpy.data.libraries):
        bpy.data.libraries.remove(library)
    bpy.ops.wm.save_as_mainfile(filepath=str((out / 'Character_An_fretting_hand_TRIAL_v545.blend').resolve()))
    print(json.dumps(report), flush=True)
    return report
