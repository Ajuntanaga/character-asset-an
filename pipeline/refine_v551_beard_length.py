"""Lengthen the existing short beard while retaining its roots and expressions."""
import json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


def build(out):
    out = Path(out)
    source = bpy.data.objects['V395_BEARD_FIBERS']
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    assert bpy.data.objects.get('V551_BEARD_FIBERS') is None
    assert not source.hide_render
    original = source.data.shape_keys.key_blocks
    skin = body.data.shape_keys.key_blocks
    assert len(original['Basis'].data) % 15 == 0
    assert all(key.name in skin for key in original)
    # The original fibers have five rings of three vertices. Work from their
    # current fitted centerlines, not the obsolete pre-proportion sample file.
    to_body = body.matrix_world.inverted() @ source.matrix_world
    to_fiber = to_body.inverted()
    body.data.calc_loop_triangles()
    coords = [v.co.copy() for v in skin['Basis'].data]
    triangles = [list(t.vertices) for t in body.data.loop_triangles
                 if all(1.50 < coords[i].z < 1.615 and coords[i].y < -.025
                        for i in t.vertices)]
    surface = BVHTree.FromPolygons(coords, triangles, all_triangles=True)
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = 'V551_BEARD_FIBERS'
    obj.data.name = obj.name
    bpy.context.scene.collection.objects.link(obj)
    assert obj.data.shape_keys is not source.data.shape_keys
    changed = skipped = moustache = 0
    before, after = [], []
    for offset in range(0, len(original['Basis'].data), 15):
        centers = [sum((to_body @ original['Basis'].data[offset + j*3+k].co
                        for k in range(3)), Vector()) / 3 for j in range(5)]
        if centers[0].z > 1.579:
            moustache += 1
            continue
        old_length = sum((b-a).length for a, b in zip(centers, centers[1:]))
        factor = min(.0024, max(.0014, old_length*1.55)) / old_length
        projected, normals, attachments = [centers[0]], [None], [None]
        for j in range(1, 5):
            target = centers[0] + (centers[j]-centers[0])*factor
            hit, normal, index, _ = surface.ray_cast(
                Vector((target.x, -.5, target.z)), Vector((0, 1, 0)))
            if hit is None or normal.y > -.10 or (hit-target).length > .004:
                break
            # Retain the existing strand's rise above the skin at each ring.
            old_hit, old_normal, _, _ = surface.find_nearest(centers[j])
            height = max(.00006, (centers[j]-old_hit).dot(old_normal))
            projected.append(hit + normal*height)
            normals.append(normal)
            ids = triangles[index]
            weights = barycentric_transform(hit, *[coords[i] for i in ids],
                                             Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
            attachments.append((ids, weights))
        if len(projected) != 5:
            skipped += 1
            continue
        for j in range(1, 5):
            tangent = (projected[min(j+1, 4)]-projected[j-1]).normalized()
            across = tangent.cross(normals[j]).normalized()
            perpendicular = across.cross(tangent).normalized()
            ids, weights = attachments[j]
            # Preserve the triangular cross section and its tapered radius.
            old_tangent = (centers[min(j+1, 4)]-centers[j-1]).normalized()
            old_across = old_tangent.cross(normals[j]).normalized()
            old_perpendicular = old_across.cross(old_tangent).normalized()
            for k in range(3):
                index = offset+j*3+k
                radial = to_body @ original['Basis'].data[index].co-centers[j]
                point = projected[j] + perpendicular*radial.dot(old_perpendicular) + across*radial.dot(old_across)
                obj.data.shape_keys.key_blocks['Basis'].data[index].co = to_fiber @ point
                for key in list(obj.data.shape_keys.key_blocks)[1:]:
                    delta = sum(((skin[key.name].data[i].co-coords[i])*w
                                 for i, w in zip(ids, weights)), Vector())
                    key.data[index].co = to_fiber @ (point+delta)
        before.append(old_length)
        after.append(sum((b-a).length for a, b in zip(projected, projected[1:])))
        changed += 1
    assert changed > 3500, (changed, skipped)
    source.hide_render = True
    source.hide_set(True)
    obj.hide_render = False
    obj.hide_set(False)
    obj.data.update()
    obj['surface_attachment'] = 'Retained roots; extended rings reattached barycentrically to current body shape keys'
    assert obj.parent == source.parent and obj.parent_bone == source.parent_bone
    assert len(obj.data.shape_keys.animation_data.drivers) == len(source.data.shape_keys.animation_data.drivers)
    bpy.context.view_layer.update()
    report = {'object': obj.name, 'retained_source': source.name,
              'changed_fibers': changed, 'skipped_fibers': skipped, 'unchanged_moustache_fibers': moustache,
              'old_length_range_m': [min(before), max(before)],
              'new_length_range_m': [min(after), max(after)],
              'shape_keys': list(obj.data.shape_keys.key_blocks.keys()),
              'main_drivers': len(rig.animation_data.drivers),
              'status': 'TRIAL_REQUIRES_VISUAL_AND_EXPRESSION_REVIEW'}
    (out / 'beard-length-report.json').write_text(json.dumps(report, indent=2))
    return report
