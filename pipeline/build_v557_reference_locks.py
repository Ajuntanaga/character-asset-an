"""Generate shared ringlet guides and a wavy undercoat on the current scalp."""
from collections import defaultdict
import math
import random

import numpy as np
from mathutils import Vector

from refine_v554_scalp_surface import part_center, part_strength


def _frame(root, face, rng):
    nape = np.clip((1.675 - root.z) / .055, 0., 1.) if root.y > -.022 else 0.
    side = np.clip((abs(root.x) - .045) / .035, 0., 1.) * np.clip((1.78 - root.z) / .07, 0., 1.)
    top = np.clip((root.z - 1.69) / .08, 0., 1.)
    normal = Vector(face['normal']).normalized()
    outward = Vector((root.x / .095**2, (root.y - .012) / .115**2,
                      (root.z - 1.682) / .118**2)).normalized()
    if normal.dot(outward) < 0:
        normal.negate()
    normal = (normal * .35 + outward * .65).normalized()
    direction = Vector((-.85, .30, .05))
    if root.x > part_center(root.y) and root.y < .035:
        direction = Vector((.25, .65, -.30))
    elif root.y > .035:
        direction = Vector((0., .65, -.50))
    direction = direction.lerp(Vector((0., .85, -.40)), float(side))
    direction = direction.lerp(Vector((0., .15, -1.)), float(nape))
    tangent = (direction - normal * direction.dot(normal)).normalized()
    across = normal.cross(tangent).normalized()
    angle = rng.uniform(-.30, .30)
    tangent = (tangent * math.cos(angle) + across * math.sin(angle)).normalized()
    across = normal.cross(tangent).normalized()
    return np.asarray(normal), np.asarray(tangent), np.asarray(across), float(nape), float(side), float(top)


def _transport_frames(center, initial_normal):
    """Keep each fiber in one bundle instead of giving it its own curl phase."""
    tangents = np.gradient(center, axis=0)
    tangents /= np.maximum(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-12)
    frames = np.empty_like(center)
    previous = initial_normal
    for j, tangent in enumerate(tangents):
        cross_section = previous - tangent * np.dot(previous, tangent)
        if np.linalg.norm(cross_section) < 1e-7:
            axis = np.eye(3)[np.argmin(np.abs(tangent))]
            cross_section = axis - tangent * np.dot(axis, tangent)
        previous = cross_section / np.linalg.norm(cross_section)
        frames[j] = previous
    return frames, np.cross(tangents, frames)


def _clear_center(center, bvh, width):
    for j, point in enumerate(center):
        near, normal, _, _ = bvh.find_nearest(Vector(point))
        if near is not None:
            clearance = (Vector(point) - near).dot(normal)
            if clearance < width[j] + .0001:
                center[j] += np.asarray(normal) * (width[j] + .0001 - clearance)


def _suspend_center(center, normal, axis, radial_u, length, t, amplitude, envelope, width):
    # A nearly tangential helix puts its inward lobe beneath the scalp. Pointwise
    # collision projection clips that whole arc into a flat band. Lift the
    # trajectory by its radial normal excursion before the BVH safety check,
    # retaining the circular lobe rather than flattening each intersecting point.
    axial_height = .0004 + np.dot(axis, normal) * length * t
    lift = np.maximum(0., width + .0001 - axial_height)
    lift += amplitude * abs(np.dot(radial_u, normal)) * envelope
    center += normal[None, :] * lift[:, None]


def _anchor(block, bvh):
    for strand in block:
        near, normal, _, _ = bvh.find_nearest(Vector(strand[0]))
        if near is not None:
            strand[0] = near + normal * .00006


def generate(roots, bvh):
    rng, nprng = random.Random(557), np.random.default_rng(557)
    # Keep the established root, radius and undercoat random streams intact.
    subclump_rng = random.Random(582)
    subclumps = 5
    # Thin once after Poisson sampling; retrying rejected candidates would fill
    # the part again. Individual fibers can overlap this interrupted scalp lane.
    dense_roots = [entry for entry in roots if rng.random() >= .72 * part_strength(entry[0])]
    macro_roots, grid = [], defaultdict(list)
    cell_size = .016
    for entry in dense_roots:
        root = entry[0]
        nape = np.clip((1.675 - root.z) / .055, 0., 1.) if root.y > -.022 else 0.
        top = np.clip((root.z - 1.69) / .08, 0., 1.)
        spacing = (.0075 + .002 * top) * (1. - nape) + .0045 * nape
        cell = tuple(math.floor(c / cell_size) for c in root)
        neighbors = (item for x in range(cell[0]-1, cell[0]+2)
                     for y in range(cell[1]-1, cell[1]+2)
                     for z in range(cell[2]-1, cell[2]+2)
                     for item in grid.get((x, y, z), ()))
        if any((point - root).length_squared < max(spacing, other_spacing)**2
               for point, other_spacing in neighbors):
            continue
        grid[cell].append((root, spacing))
        macro_roots.append(entry)

    steps = 41
    t = np.linspace(0., 1., steps)
    points, radii, uvs = [], [], []
    macro_strands = 0
    for root, face, weights in macro_roots:
        normal, tangent, across, nape, side, top = _frame(root, face, rng)
        children = round((140 + 80 * top) * (1. - nape) + 28 * nape)
        length = rng.uniform(.0085, .014) * (.70 + .30 * top) * (1. - .15 * side)
        length = length * (1. - nape) + rng.uniform(.003, .006) * nape
        # V571's broad curl loops read as tiled ribbons. Reduce only their
        # radial excursion; retain guide spacing, fiber density and width.
        amplitude = rng.uniform(.0032, .0045) * (.65 + .35 * top) * (1. - .18 * side) * (1. - .75 * nape)
        phase = rng.uniform(-math.pi, math.pi)
        turn = rng.uniform(.60, .85) * (1. - .25 * nape) * (-1 if rng.random() < .45 else 1)
        # V564's upright full helices read as repeated springs. Lay partial
        # curls along the scalp so neighboring bundles overlap in the growth
        # direction. Keep density, bundle width and true fiber radii unchanged.
        tilt = rng.uniform(math.radians(68), math.radians(78))
        tilt = tilt * (1. - nape) + math.radians(75) * nape
        axis = normal * math.cos(tilt) + tangent * math.sin(tilt)
        radial_u = tangent - axis * np.dot(tangent, axis)
        radial_u /= np.linalg.norm(radial_u)
        radial_v = np.cross(axis, radial_u)
        warped_t = t + rng.uniform(-.035, .035) * np.sin(math.pi * t)
        angle = phase + math.tau * turn * warped_t
        envelope = (1. - np.exp(-t / .07)) * (1. - .15 * t**2)
        radial = (radial_u[None, :] * np.cos(angle)[:, None]
                  + radial_v[None, :] * np.sin(angle)[:, None])
        center = (np.asarray(root)[None, :] + normal[None, :] * .0004
                  + axis[None, :] * (length * t)[:, None]
                  + radial * (amplitude * envelope)[:, None])
        # Reference locks overlap at the 9.5mm root spacing. V562's narrow
        # bundles left smooth scalp exposed between isolated wire-like loops.
        # Add fibers and bundle volume together; individual radii stay real.
        width = rng.uniform(.00115, .00175) * (1. - .35 * side) * (1. - .72 * nape)
        spread = (.65 + .45 * np.sin(math.pi * t)) * (1. - .90 * t**3)
        _suspend_center(center, normal, axis, radial_u, length, t,
                        amplitude, envelope, width * spread)
        _clear_center(center, bvh, width * spread)
        u, v = _transport_frames(center, normal)
        disk_angle = nprng.uniform(0., math.tau, children)
        disk_radius = np.sqrt(nprng.uniform(0., 1., children)) * width
        offsets = (np.cos(disk_angle)[:, None, None] * u[None, :, :]
                   + np.sin(disk_angle)[:, None, None] * v[None, :, :])
        block = center[None, :, :] + offsets * disk_radius[:, None, None] * spread[None, :, None]
        # Hundreds of fibers on one identical trajectory read as a molded C.
        # Split that trajectory into five related locks, preserving each root
        # and the existing density, fiber radii and macro guide distribution.
        # The smooth departure also avoids a kink at the anchored first point.
        departure = (1. - np.exp(-t / .10))**2
        fiber_v = np.broadcast_to(v, block.shape).copy()
        for group in range(subclumps):
            selected = np.arange(group, children, subclumps)
            group_amplitude = amplitude * subclump_rng.uniform(.85, 1.15)
            group_turn = turn * subclump_rng.uniform(.88, 1.12)
            phase_warp = subclump_rng.uniform(-.35, .35) * np.sin(math.pi * t)
            group_angle = phase + math.tau * group_turn * warped_t + phase_warp
            group_radial = (radial_u[None, :] * np.cos(group_angle)[:, None]
                            + radial_v[None, :] * np.sin(group_angle)[:, None])
            group_center = (np.asarray(root)[None, :] + normal[None, :] * .0004
                            + axis[None, :] * (length * t)[:, None]
                            + group_radial * (group_amplitude * envelope)[:, None])
            _suspend_center(group_center, normal, axis, radial_u, length, t,
                            group_amplitude, envelope, width * spread)
            _clear_center(group_center, bvh, width * spread)
            group_u, group_v = _transport_frames(group_center, normal)
            group_offsets = (np.cos(disk_angle[selected])[:, None, None] * group_u[None, :, :]
                             + np.sin(disk_angle[selected])[:, None, None] * group_v[None, :, :])
            group_block = (group_center[None, :, :]
                           + group_offsets * disk_radius[selected, None, None] * spread[None, :, None])
            block[selected] += (group_block - block[selected]) * departure[None, :, None]
            fiber_v[selected] = group_v
        # Small, tapered child departures avoid the perfectly parallel bands
        # without returning to the previously rejected independent wire coils.
        wave = nprng.uniform(.00010, .00030, children)[:, None] * np.sin(
            nprng.uniform(0., math.tau, children)[:, None] + math.tau * 1.4 * t[None, :])
        block += fiber_v * (wave * np.sin(math.pi * t)[None, :])[:, :, None]
        _anchor(block, bvh)
        radius = nprng.uniform(.000034, .000048, children)[:, None] * (1. - .85 * t**2)[None, :]
        radius[:, -1] = .000003
        points.append(block.astype(np.float32))
        radii.append(radius.astype(np.float32))
        uvs.append(np.tile(np.asarray(weights) @ np.asarray(face['uv']), (children, 1)))
        macro_strands += children

    # Dense short waves break up the underlay without drawing another layer of
    # visible hollow coils. They follow the same local growth direction.
    base_children = 32
    for root, face, weights in dense_roots:
        normal, tangent, across, nape, side, top = _frame(root, face, rng)
        phase = nprng.uniform(-math.pi, math.pi, base_children)[:, None]
        length = nprng.uniform(.007, .013, base_children)[:, None] * (1. - .72 * nape)
        amplitude = nprng.uniform(.0006, .0010, base_children)[:, None] * (1. - .65 * nape)
        height = .00015 + np.sin(math.pi * t)[None, :] * nprng.uniform(.0008, .0018, base_children)[:, None] * (1. - .65 * nape)
        lateral = amplitude * np.sin(math.pi * t)[None, :] * np.sin(phase + math.pi * t[None, :])
        block = (np.asarray(root)[None, None, :] + tangent[None, None, :] * (length * t[None, :])[:, :, None]
                 + normal[None, None, :] * height[:, :, None] + across[None, None, :] * lateral[:, :, None])
        spread = .0018 * (1. - .35 * nape)
        offsets = (nprng.uniform(-spread, spread, base_children)[:, None] * across[None, :]
                   + nprng.uniform(-spread, spread, base_children)[:, None] * tangent[None, :])
        block += offsets[:, None, :]
        # Undercoat is close to the scalp; check its actual fibers, not a wide
        # bundle center whose offsets could still pass through the surface.
        for strand in block:
            for j, point in enumerate(strand):
                near, n, _, _ = bvh.find_nearest(Vector(point))
                if near is not None:
                    clearance = (Vector(point) - near).dot(n)
                    if clearance < .00007:
                        strand[j] += np.asarray(n) * (.00007 - clearance)
        _anchor(block, bvh)
        radius = nprng.uniform(.000032, .000044, base_children)[:, None] * (1. - .80 * t**2)[None, :]
        radius[:, -1] = .000003
        points.append(block.astype(np.float32))
        radii.append(radius.astype(np.float32))
        uvs.append(np.tile(np.asarray(weights) @ np.asarray(face['uv']), (base_children, 1)))

    points, radii, uvs = np.concatenate(points), np.concatenate(radii), np.concatenate(uvs).astype(np.float32)
    assert np.isfinite(points).all() and np.isfinite(radii).all()
    assert 100 < len(macro_roots) < len(dense_roots)
    report = {'geometry_model': 'V584_suspended_partial_curl_trajectories',
              'guides': len(macro_roots), 'undercoat_guides': len(dense_roots),
              'primary_strands': macro_strands, 'undercoat_strands': len(dense_roots) * base_children,
              'top_root_spacing_m': .0095, 'side_root_spacing_m': .0075,
              'posterior_root_spacing_m': .0045, 'posterior_guides': sum(
                  root.z < 1.655 and root.y > -.022 for root, _, _ in macro_roots),
              'top_lock_axial_length_m': [.0085, .014], 'partial_turns': [.60, .85],
              'top_lock_amplitude_m': [.0032, .0045],
              'axis_tilt_from_scalp_normal_degrees': [68, 78],
              'top_bundle_radius_m': [.00115, .00175],
              'maximum_primary_fibers_per_guide': 220,
              'undercoat_fibers_per_guide': base_children,
              'undercoat_lift_m': [.0008, .0018],
              'child_departure_amplitude_m': [.00010, .00030],
              'trajectory_subclumps_per_guide': subclumps,
              'subclump_amplitude_factor': [.85, 1.15],
              'subclump_turn_factor': [.88, 1.12],
              'subclump_phase_warp_radians': [-.35, .35],
              'guide_clearance': 'analytic radial suspension before BVH safety projection',
              'independent_fiber_coils': False,
              'fiber_frames': 'parallel_transport', 'part_maximum_root_thinning': .72}
    return points, radii, uvs, report


def reduce_skin_microrelief():
    """Keep the original photo atlas; lower only the inherited synthetic pores."""
    import bpy
    report = {}
    for name in ('V372_FACE_SKIN', 'V377_REFERENCE_PHOTO_SKIN', 'V365_LID_SKIN'):
        material = bpy.data.materials[name]
        bump = next(n for n in material.node_tree.nodes if n.type == 'BUMP')
        previous = {'distance': bump.inputs['Distance'].default_value}
        if bump.inputs['Strength'].is_linked:
            factor = bump.inputs['Strength'].links[0].from_node
            assert factor.type == 'MATH' and factor.operation == 'MULTIPLY'
            assert not factor.inputs[1].is_linked
            previous['strength_factor'] = factor.inputs[1].default_value
            factor.inputs[1].default_value = .04
        else:
            previous['strength_factor'] = bump.inputs['Strength'].default_value
            bump.inputs['Strength'].default_value = .04
        bump.inputs['Distance'].default_value = .000020
        report[name] = {'previous': previous, 'trial_strength_factor': .04,
                        'trial_distance': .000020, 'albedo_changed': False}
    return report
