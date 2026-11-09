"""Fit a licensed BlenderKit garment to the existing character without replacing it."""
from pathlib import Path
import json
import math
import bpy
import numpy as np
from mathutils import Matrix
from mathutils.kdtree import KDTree

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
STAGE = ROOT / 'production_v344_free_asset_wardrobe'
STAGE.mkdir(exist_ok=True)
SOURCE = 'V344_SOURCE_Unisex Denim Shirt Design'
NAME = 'V344_FITTED_CHARCOAL_DENIM_JACKET'


def smooth(a):
    a = np.clip(a, 0., 1.)
    return a * a * (3. - 2. * a)


def main():
    source = bpy.data.objects[SOURCE]
    old = bpy.data.objects.get(NAME)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    collection = bpy.data.collections.get('V344_FITTED_WARDROBE')
    if not collection:
        collection = bpy.data.collections.new('V344_FITTED_WARDROBE')
        bpy.context.scene.collection.children.link(collection)
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = NAME
    collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_set(False)
    obj.matrix_world = Matrix.Identity(4)
    n = len(obj.data.vertices)
    xyz = np.empty(n * 3, dtype=np.float32)
    obj.data.vertices.foreach_get('co', xyz)
    xyz = xyz.reshape(-1, 3).astype(np.float64)

    # The source has disconnected sewn pattern pieces. Classify whole pieces,
    # then attach fine stitching/buttons to the nearest substantial panel.
    parents = np.arange(n, dtype=np.int32)
    def find(x):
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    edges = np.empty(len(obj.data.edges) * 2, dtype=np.int32)
    obj.data.edges.foreach_get('vertices', edges)
    for a, b in edges.reshape(-1, 2):
        a, b = find(a), find(b)
        if a != b:
            parents[b] = a
    labels = np.array([find(i) for i in range(n)])
    roots, inverse, counts = np.unique(labels, return_inverse=True, return_counts=True)
    is_sleeve = np.zeros(n, dtype=bool)
    large = np.zeros(n, dtype=bool)
    classified = []
    for k, count in enumerate(counts):
        indices = np.flatnonzero(inverse == k)
        points = xyz[indices]
        sleeve = bool(points[:, 2].max() < .56 and (
            np.mean(np.abs(points[:, 0])) > .160 or
            (points[:, 2].min() > .380
             and np.mean(np.abs(points[:, 0])) > .140)))
        if count > 500:
            large[indices] = True
            is_sleeve[indices] = sleeve
            classified.append({'vertices': int(count), 'sleeve': sleeve})
    tree = KDTree(int(large.sum()))
    for idx in np.flatnonzero(large):
        tree.insert(xyz[idx], int(idx))
    tree.balance()
    for k, count in enumerate(counts):
        if count > 500:
            continue
        indices = np.flatnonzero(inverse == k)
        # Fine seam islands must move as a unit. Per-vertex classification
        # splits long stitches between torso and sleeve and creates spikes.
        nearest_votes = [is_sleeve[tree.find(xyz[idx])[1]]
                         for idx in indices[::max(1, len(indices) // 32)]]
        is_sleeve[indices] = np.mean(nearest_votes) > .5

    # Torso fit preserves the authored cloth volume and UVs. Rotate the sleeves
    # from the source's relaxed pose onto the existing mesh's actual arm line.
    torso = xyz * np.array([1.13, 1.40, .99]) + [0., -.050, .950]
    fitted = torso.copy()
    for side in (-1., 1.):
        mask = is_sleeve & (xyz[:, 0] * side > 0)
        p = xyz[mask].copy()
        p[:, 0] *= side
        source_pivot = np.array([.152, .035, .520])
        target_pivot = np.array([.17176, -.001, 1.4648])
        angle = math.radians(-47.)
        rotation = np.array([[math.cos(angle), 0., math.sin(angle)],
                             [0., 1., 0.],
                             [-math.sin(angle), 0., math.cos(angle)]])
        moved = (p - source_pivot) * [1.04, 1.12, 1.04]
        moved = moved @ rotation.T + target_pivot
        moved[:, 0] *= side
        weight = smooth((.565 - p[:, 2]) / .115)[:, None]
        fitted[mask] = torso[mask] * (1. - weight) + moved * weight
    obj.data.vertices.foreach_set('co', fitted.astype(np.float32).ravel())
    obj.data.update()
    for polygon in obj.data.polygons:
        polygon.use_smooth = True

    # Retain the asset's actual seam/normal textures; shift the blue fabric
    # toward the reference's charcoal denim rather than replacing it by noise.
    for index, original in enumerate(list(obj.data.materials)):
        material = original.copy()
        material.name = 'V344_CHARCOAL_' + original.name
        obj.data.materials[index] = material
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        prior = list(bsdf.inputs['Base Color'].links)
        if prior:
            src = prior[0].from_socket
            links.remove(prior[0])
            hsv = nodes.new('ShaderNodeHueSaturation')
            hsv.inputs['Saturation'].default_value = .16
            hsv.inputs['Value'].default_value = .025
            links.new(src, hsv.inputs['Color'])
            links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = .84
        bsdf.inputs['Specular IOR Level'].default_value = .25
        if 'Sheen Weight' in bsdf.inputs:
            bsdf.inputs['Sheen Weight'].default_value = .015
        for node in nodes:
            if node.type == 'NORMAL_MAP':
                node.inputs['Strength'].default_value = .30

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    decimate = obj.modifiers.new('V344_REDUCE_SEWN_SOURCE', 'DECIMATE')
    decimate.ratio = .40
    decimate.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=decimate.name)
    body = bpy.data.objects['V322_MB_MALE_BODY']
    rig = bpy.data.objects['V322_MB_MALE_RIG']
    # The body and old shirt are masked/open surfaces. Global OUTSIDE
    # shrinkwrap misclassifies them and collapses the authored collar/volume.
    for group in body.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    transfer = obj.modifiers.new('V344_BODY_DEFORMATION_WEIGHTS', 'DATA_TRANSFER')
    transfer.object = body
    transfer.use_vert_data = True
    transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    transfer.vert_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    armature = obj.modifiers.new('V344_EXISTING_CHARACTER_RIG', 'ARMATURE')
    armature.object = rig
    armature.use_deform_preserve_volume = True
    obj['asset_source'] = 'BlenderKit / Wearable3D / Unisex Denim Shirt Design'
    obj['asset_license'] = 'BlenderKit Royalty Free; no standalone asset redistribution'
    obj['asset_version_id'] = '2ea0e990-f222-4aca-9067-6529f9f00c2e'
    obj['fit_status'] = 'VISUAL_REVIEW_REQUIRED; existing body/rig alignment needs animation validation'
    scene = bpy.context.scene
    scene['V344_STATUS'] = 'FREE_AUTHORED_DENIM_GARMENT_FITTED_VISUAL_REVIEW_REQUIRED'
    bpy.ops.file.pack_all()
    output = STAGE / 'Character_An_free_asset_wardrobe_v344.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    report = {'output': str(output), 'source_vertices': n,
              'fitted_vertices': len(obj.data.vertices), 'fitted_faces': len(obj.data.polygons),
              'sleeve_vertices': int(is_sleeve.sum()), 'large_panels': classified,
              'weight_groups': len(obj.vertex_groups),
              'unweighted_vertices': sum(not v.groups for v in obj.data.vertices)}
    (STAGE / 'fit_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != 'large_panels'}))


if __name__ == '__main__':
    main()
