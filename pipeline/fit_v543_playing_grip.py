"""Fit a supported picking grip against evaluated skin, retaining native rigging."""
import bpy
import json
import math
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v543_supported_grip'
OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).parent.name == 'production_v542_index_curl'
scene = bpy.context.scene
main = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
rig = bpy.data.objects['V528_NATIVE_RIG.R']
hand = bpy.data.objects['V528_NATIVE_HAND.R']
pick = bpy.data.objects['V361_NYLON_PICK']
assert len(main.animation_data.drivers) == 1957
thumb = [rig.pose.bones[f'DEF-Finger_Thumb{j}.R'] for j in (1, 2, 3)]
index = [main.pose.bones[f'FK-Finger_Index{j}.R'] for j in (1, 2, 3)]
original = [(b, b.rotation_mode, b.matrix_basis.copy()) for b in thumb + index]
pick_inverse = pick.matrix_parent_inverse.copy()
pick_world = pick.matrix_world.copy()
subdivision = [(m, m.levels) for m in hand.modifiers if m.type == 'SUBSURF']
rest = rig.data.bones
along = (rest['DEF-Finger_Middle1.R'].head_local - rest['DEF-Hand.R'].head_local).normalized()
across = (rest['DEF-Finger_Index1.R'].head_local - rest['DEF-Finger_Pinky1.R'].head_local).normalized()
palm_normal = across.cross(along).normalized()
axes = [b.bone.matrix_local.to_3x3().inverted() @ palm_normal.cross(b.bone.tail_local - b.bone.head_local).normalized() for b in thumb]
opposition = thumb[0].bone.matrix_local.to_3x3().inverted() @ palm_normal
nails = {i for p in hand.data.polygons if p.material_index == 1 for i in p.vertices}
tb = rest['DEF-Finger_Thumb3.R']
group = hand.vertex_groups[tb.name].index
nail_ids = [v.index for v in hand.data.vertices if v.index in nails and any(g.group == group and g.weight > .6 for g in v.groups)]
nail_center = sum((hand.data.vertices[i].co for i in nail_ids), Vector()) / len(nail_ids)
radials = {}
for name, direction in [(tb.name, tb.head_local - nail_center), ('DEF-Finger_Index3.R', tb.head_local - rest['DEF-Finger_Index3.R'].head_local)]:
    b = rest[name]
    axis = (b.tail_local - b.head_local).normalized()
    radial = (direction - axis * direction.dot(axis)).normalized()
    radials[name] = b.matrix_local.to_3x3().inverted() @ radial


def apply(values):
    for j, b in enumerate(thumb):
        b.rotation_mode = 'QUATERNION'
        b.rotation_quaternion = Quaternion(axes[j], float(values[0 if j == 0 else j + 1]))
        if j == 0:
            b.rotation_quaternion = Quaternion(opposition, float(values[1])) @ b.rotation_quaternion
    for j, b in enumerate(index):
        b.rotation_euler.x = float(values[j + 4])
    bpy.context.view_layer.update()


def skin_tree():
    evaluated = hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons])
    finally:
        evaluated.to_mesh_clear()


def contact(tree, name):
    bone = rig.pose.bones[name]
    matrix = rig.matrix_world @ bone.matrix
    center = matrix @ Vector((0, bone.bone.length * .57, 0))
    direction = (matrix.to_3x3() @ radials[name]).normalized()
    point, normal, face, distance = tree.ray_cast(center, direction, .025)
    if point is None:
        raise RuntimeError(f'No skin ray from {name}')
    if normal.dot(direction) < 0:
        normal.negate()
    return np.array(point), np.array(normal)

prior = np.radians([18, 24, 32, 15, 55, 68, 35])
low = np.radians([-30, -45, -15, -15, 42, 55, 22])
high = np.radians([45, 65, 65, 55, 68, 78, 50])
x = prior.copy()
points = [pick_world @ v.co for v in pick.data.vertices]
old_tip = (points[0] + points[48]) / 2
old_back = (points[24] + points[72]) / 2
old_normal = (points[48] - points[0]).normalized()
old_axis = (old_tip - old_back).normalized()
thickness = (points[48] - points[0]).length


def residual(values):
    apply(values)
    tree = skin_tree()
    t, tn = contact(tree, 'DEF-Finger_Thumb3.R')
    i, inn = contact(tree, 'DEF-Finger_Index3.R')
    return np.r_[t - i - inn * (thickness + .0001), .004 * (tn + inn), (values - prior) * np.array([.0004] * 4 + [.001] * 3)]

camera = scene.camera
camera_matrix = camera.matrix_world.copy()
camera_scale = camera.data.ortho_scale
success = False
try:
    for m, _ in subdivision:
        m.levels = 1
    for iteration in range(18):
        r = residual(x)
        columns = []
        for j in range(len(x)):
            v = x.copy(); v[j] += .003
            columns.append((residual(v) - r) / .003)
        jacobian = np.array(columns).T
        delta = np.linalg.solve(jacobian.T @ jacobian + np.eye(len(x)) * 1e-7, -jacobian.T @ r)
        delta = np.clip(delta, -.2, .2)
        best = (float(r @ r), x.copy())
        for rate in (1, .5, .2):
            v = np.clip(x + delta * rate, low, high)
            rr = residual(v)
            if float(rr @ rr) < best[0]:
                best = (float(rr @ rr), v)
        if np.linalg.norm(best[1] - x) < 1e-5:
            break
        x = best[1]
    apply(x)
    for m, level in subdivision:
        m.levels = level
    bpy.context.view_layer.update()
    tree = skin_tree()
    t, tn = contact(tree, 'DEF-Finger_Thumb3.R')
    i, inn = contact(tree, 'DEF-Finger_Index3.R')
    seat = Vector((t + i) / 2)
    normal = Vector(inn - tn).normalized()
    # Expose the point on the outside of the index/thumb pinch, away from palm.
    wrist = rig.matrix_world @ rig.pose.bones['DEF-Hand.R'].head
    direction = seat - wrist
    direction = (direction - normal * direction.dot(normal)).normalized()
    first = old_normal.rotation_difference(normal)
    rotated_axis = first @ old_axis
    angle = math.atan2(normal.dot(rotated_axis.cross(direction)), rotated_axis.dot(direction))
    rotation = Quaternion(normal, angle) @ first
    old_contact = old_tip - old_axis * .013
    world = Matrix.Translation(seat) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-old_contact) @ pick_world
    parent_frame = rig.matrix_world @ rig.pose.bones['DEF-Hand.R'].matrix @ Matrix.Translation((0, rest['DEF-Hand.R'].length, 0))
    pick.matrix_parent_inverse = parent_frame.inverted() @ world
    pick.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    tip = pick.matrix_world @ ((pick.data.vertices[0].co + pick.data.vertices[48].co) / 2)
    report = {'angles_deg': np.degrees(x).tolist(), 'iterations': iteration + 1,
              'thumb_contact': t.tolist(), 'index_contact': i.tolist(),
              'contact_separation_m': float(np.linalg.norm(t - i)),
              'normal_dot': float(tn @ inn), 'pick_thickness_m': thickness,
              'skin_distance_from_tip_m': tree.find_nearest(tip)[3],
              'drivers': len(main.animation_data.drivers),
              'status': 'EVALUATED_SKIN_FIT_REQUIRES_VISUAL_REVIEW'}
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 850; scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    for name, offset in [('front', (.13, -.2, .04)), ('side', (-.12, -.18, .06))]:
        camera.location = seat + Vector(offset)
        camera.rotation_euler = (seat - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = .18
        scene.render.filepath = str(OUT / f'{name}.png')
        bpy.ops.render.render(write_still=True)
    (OUT / 'contact.json').write_text(json.dumps(report, indent=2))
    camera.matrix_world = camera_matrix; camera.data.ortho_scale = camera_scale
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'Character_An_supported_grip_TRIAL_v543.blend'))
    success = True
    print(json.dumps(report))
finally:
    camera.matrix_world = camera_matrix; camera.data.ortho_scale = camera_scale
    for m, level in subdivision:
        m.levels = level
    if not success:
        for b, mode, basis in original:
            b.rotation_mode = mode; b.matrix_basis = basis
        pick.matrix_parent_inverse = pick_inverse
        bpy.context.view_layer.update()
