"""Fit the downloaded CC0 wardrobe onto An's existing body and rig."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
STAGE = ROOT / 'production_v345_tailored_free_wardrobe'
STAGE.mkdir(exist_ok=True)
BODY = bpy.data.objects['V322_MB_MALE_BODY']
RIG = bpy.data.objects['V322_MB_MALE_RIG']
REPORT = {}


def world_coords(obj):
    return np.array([obj.matrix_world @ v.co for v in obj.data.vertices])


def bvh_of(obj, evaluated=False):
    evaluated_obj = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else obj
    mesh = evaluated_obj.to_mesh() if evaluated else obj.data
    tree = BVHTree.FromPolygons(
        [evaluated_obj.matrix_world @ v.co for v in mesh.vertices],
        [p.vertices[:] for p in mesh.polygons])
    if evaluated:
        evaluated_obj.to_mesh_clear()
    return tree


BODY_TREE = bvh_of(BODY)


def clearance(points, tree, gap, max_depth=.13):
    corrected = points.copy()
    count, max_move = 0, 0.
    for index, p in enumerate(points):
        q, normal, face, distance = tree.find_nearest(Vector(p))
        if q is None:
            continue
        signed = (Vector(p) - q).dot(normal)
        if -max_depth < signed < gap:
            # The intact, unmasked anatomical body supplies outward normals.
            # Only lift penetrations; retain the garment's authored ease/folds.
            delta = normal * (gap - signed)
            corrected[index] += np.array(delta)
            count += 1
            max_move = max(max_move, delta.length)
    return corrected, {'vertices_lifted': count, 'max_lift_m': max_move}


def collection():
    result = bpy.data.collections.get('V345_TAILORED_FREE_WARDROBE')
    if result is None:
        result = bpy.data.collections.new('V345_TAILORED_FREE_WARDROBE')
        bpy.context.scene.collection.children.link(result)
    return result


def duplicate(source, name):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    collection().objects.link(obj)
    obj.hide_render = False
    obj.hide_set(False)
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    obj.modifiers.clear()
    if obj.data.shape_keys:
        obj.shape_key_clear()
    return obj


def write_coords(obj, points):
    obj.data.vertices.foreach_set('co', np.asarray(points, dtype=np.float32).ravel())
    obj.data.update()
    for face in obj.data.polygons:
        face.use_smooth = True


def bind_body_weights(obj):
    obj.vertex_groups.clear()
    for group in BODY.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    transfer = obj.modifiers.new('An anatomical skin weights', 'DATA_TRANSFER')
    transfer.object = BODY
    transfer.use_vert_data = True
    transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    transfer.vert_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    armature = obj.modifiers.new('An existing performance rig', 'ARMATURE')
    armature.object = RIG
    armature.use_deform_preserve_volume = True


def source_item(kind):
    return max((o for o in bpy.data.objects if o.type == 'MESH' and
                o.name.startswith('V344_CC0_SOURCE_' + kind)),
               key=lambda o: len(o.data.vertices))


def target_bones():
    # Measured anatomical centerlines, in meters, from the retained body.
    result = {
        'pelvis': ((0, -.015, .970), (0, .013, 1.075)),
        'spine_01': ((0, .013, 1.075), (0, .009, 1.158)),
        'spine_02': ((0, .009, 1.158), (0, .030, 1.298)),
        'spine_03': ((0, .030, 1.298), (0, .030, 1.490)),
        'neck_01': ((0, -.008, 1.544), (0, -.043, 1.625)),
        'head': ((0, -.043, 1.625), (0, -.040, 1.800)),
    }
    for suffix, side in (('l', 1), ('r', -1)):
        arm = {
            'clavicle': ((.022, -.009, 1.493), (.170, .003, 1.427)),
            'upperarm': ((.170, .003, 1.427), (.397, -.006, 1.296)),
            'lowerarm': ((.397, -.006, 1.296), (.616, -.030, 1.186)),
            'hand': ((.616, -.030, 1.186), (.675, -.067, 1.134)),
            'thigh': ((.1085, -.012, .976), (.1431, -.0006, .511)),
            'calf': ((.1431, -.0006, .511), (.1790, .027, .103)),
            'foot': ((.1790, .027, .103), (.1890, -.116, .024)),
            'ball': ((.1890, -.116, .024), (.1830, -.212, .021)),
        }
        for name, pair in arm.items():
            result[name + '_' + suffix] = tuple((p[0] * side, p[1], p[2]) for p in pair)
    return result


def fit_cc0(kind, name, gap):
    source = source_item(kind)
    obj = duplicate(source, name)
    points = world_coords(source)
    source_rig = source.parent
    destinations = target_bones()
    transforms = {}
    for bone_name, (head, tail) in destinations.items():
        bone = source_rig.data.bones.get(bone_name)
        if not bone:
            continue
        a = source_rig.matrix_world @ bone.head_local
        b = source_rig.matrix_world @ bone.tail_local
        h, t = Vector(head), Vector(tail)
        rotation = (b-a).rotation_difference(t-h).to_matrix()
        longitudinal = (t-h).length / (b-a).length
        axis = np.array((b-a).normalized())
        # Length and girth are independent: preserve generous cloth volume.
        girth = 1.12 if kind != 'boots' else 1.04
        stretch = girth * np.eye(3) + (longitudinal-girth) * np.outer(axis, axis)
        matrix = np.array(rotation) @ stretch
        transforms[bone_name] = (matrix, np.array(h) - matrix @ np.array(a))
    fitted = np.zeros_like(points)
    weights = np.zeros(len(points))
    for v in source.data.vertices:
        for assignment in v.groups:
            group = source.vertex_groups[assignment.group].name
            if group not in transforms:
                continue
            linear, offset = transforms[group]
            w = assignment.weight
            fitted[v.index] += w * (linear @ points[v.index] + offset)
            weights[v.index] += w
    valid = weights > .0001
    fitted[valid] /= weights[valid, None]
    fitted[~valid] = points[~valid] * [1.10, 1.10, 1.11]
    fitted, corrected = clearance(fitted, BODY_TREE, gap)
    if kind == 'jeans':
        # Straight leg rather than leggings; the hem must clear the boot shaft.
        lower = fitted[:, 2] < .48
        centers = np.sign(fitted[:, 0]) * np.interp(fitted[:, 2], [.10, .51], [.179, .143])
        center_y = np.interp(fitted[:, 2], [.10, .51], [.027, -.001])
        ease = .012 * np.clip((.50-fitted[:, 2])/.20, 0, 1)
        dx, dy = fitted[:, 0]-centers, fitted[:, 1]-center_y
        radius = np.sqrt(dx*dx+dy*dy)
        scale = 1 + ease / np.maximum(radius, .025)
        fitted[lower, 0] = centers[lower] + dx[lower]*scale[lower]
        fitted[lower, 1] = center_y[lower] + dy[lower]*scale[lower]
    write_coords(obj, fitted)
    obj.data.materials.clear()
    if kind == 'shirt':
        material = bpy.data.materials['V325_DARK_FLORAL_COTTON'].copy()
        material.name = 'V345_FLORAL_COTTON_ON_AUTHORED_COLLAR'
        for node in material.node_tree.nodes:
            if node.type == 'MAPPING':
                node.inputs['Scale'].default_value = (2.4, 2.4, 2.4)
        obj.data.materials.append(material)
    else:
        for original in source.data.materials:
            material = original.copy()
            material.name = 'V345_' + kind.upper() + '_' + original.name
            nodes, links = material.node_tree.nodes, material.node_tree.links
            bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
            old_links = list(bsdf.inputs['Base Color'].links)
            if old_links:
                incoming = old_links[0].from_socket
                links.remove(old_links[0])
                tint = nodes.new('ShaderNodeMixRGB')
                tint.blend_type = 'MULTIPLY'
                tint.inputs[0].default_value = 1
                tint.inputs[2].default_value = ((.008, .008, .008, 1) if kind == 'jeans'
                                                 else (.20, .085, .033, 1))
                links.new(incoming, tint.inputs[1])
                links.new(tint.outputs[0], bsdf.inputs['Base Color'])
            else:
                bsdf.inputs['Base Color'].default_value = ((.012, .014, .017, 1) if kind == 'jeans'
                                                           else (.055, .025, .010, 1))
            bsdf.inputs['Roughness'].default_value = .78 if kind == 'jeans' else .40
            obj.data.materials.append(material)
    bind_body_weights(obj)
    subdivision = obj.modifiers.new('Smooth authored garment topology', 'SUBSURF')
    subdivision.levels = 1
    subdivision.render_levels = 2
    if kind != 'boots':
        solidify = obj.modifiers.new('Fabric edge thickness', 'SOLIDIFY')
        solidify.thickness = .0015
        solidify.offset = 0
    obj['source_license'] = 'CC0-1.0, MakeHuman / kblood CharacterCreator generated assets'
    obj['fit_status'] = 'REST_FIT_REQUIRES_VISUAL_REVIEW; ANIMATION_NOT_YET_VALIDATED'
    REPORT[kind] = dict(vertices=len(points), unhandled_weights=int((~valid).sum()), **corrected)
    return obj


def fit_jacket(shirt):
    source = bpy.data.objects['V344_FITTED_CHARCOAL_DENIM_JACKET']
    obj = duplicate(source, 'V345_TAILORED_CHARCOAL_DENIM_JACKET')
    points = world_coords(source)
    # Move the rotated sleeves onto the measured body arm centerline.
    arm_weight = np.clip((np.abs(points[:, 0])-.18)/.12, 0, 1)
    points[:, 2] -= .038 * arm_weight
    points[:, 1] -= .016 * arm_weight
    points, body_fit = clearance(points, BODY_TREE, .012)
    # Shirt is already outside the body. Restrict the second lift to its torso
    # and sleeves, avoiding nearest-surface extrapolation across the open hem.
    bpy.context.view_layer.update()
    # A solidified shirt has inward-facing inner polygons. Using those for a
    # signed-distance check incorrectly treats an intersecting jacket as clear.
    thickness = next(m for m in shirt.modifiers if m.type == 'SOLIDIFY')
    thickness.show_viewport = False
    bpy.context.view_layer.update()
    shirt_tree = bvh_of(shirt, evaluated=True)
    points, shirt_fit = clearance(points, shirt_tree, .012, max_depth=.085)
    thickness.show_viewport = True
    write_coords(obj, points)
    bind_body_weights(obj)
    obj['asset_license'] = source['asset_license']
    obj['asset_source'] = source['asset_source']
    obj['fit_status'] = 'VISUAL_REVIEW_REQUIRED'
    REPORT['jacket'] = {'vertices': len(points), 'body_clearance': body_fit, 'shirt_clearance': shirt_fit}
    source.hide_render = True
    source.hide_set(True)
    return obj


def main():
    # Hide the rejected body-derived shells without deleting prior work.
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(('V325_', 'V326_', 'V337_')) and obj.type in {'MESH', 'CURVE'}:
            obj.hide_render = True
            obj.hide_set(True)
    shirt = fit_cc0('shirt', 'V345_CC0_FITTED_FLORAL_SHIRT', .007)
    fit_cc0('jeans', 'V345_CC0_FITTED_STRAIGHT_JEANS', .011)
    fit_cc0('boots', 'V345_CC0_FITTED_BROWN_BOOTS', .004)
    fit_jacket(shirt)
    # The head shares the historical V326 prefix with obsolete clothing.
    head = bpy.data.objects['V326_PHOTOREAL_FACEBUILDER_HEAD']
    head.hide_render = False
    head.hide_set(False)
    bpy.context.scene['V345_STATUS'] = 'FREE_WARDROBE_FITTED_PENDING_VISUAL_REVIEW'
    bpy.ops.file.pack_all()
    destination = STAGE / 'Character_An_tailored_free_wardrobe_v345.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), check_existing=False)
    REPORT['output'] = str(destination)
    (STAGE / 'fit_report.json').write_text(json.dumps(REPORT, indent=2))
    print(json.dumps(REPORT))


if __name__ == '__main__':
    main()
