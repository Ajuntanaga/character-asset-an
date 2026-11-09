"""Feather the polygon hair mask into nearby clean scalp colour, reversibly."""
import json
from collections import defaultdict
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def build(output, width=.005):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    mesh = body.data
    assert not mesh.attributes.get('V548_HairCoverage')
    original = bpy.data.materials['V371_DARK_HAIR_UNDERLAY']
    original_index = list(mesh.materials).index(original)
    skin = bpy.data.materials['V377_REFERENCE_PHOTO_SKIN']
    skin_indices = {0, list(mesh.materials).index(skin)}
    basis = mesh.shape_keys.key_blocks['Basis'].data
    hair_faces = [p for p in mesh.polygons if p.material_index == original_index]
    hair_vertices = {v for p in hair_faces for v in p.vertices}
    # UV seams duplicate vertices. Classify coincident points together so those
    # seams do not accidentally become bald stripes within the hair cap.
    def key(i):
        return tuple(round(c, 5) for c in basis[i].co)

    skin_loops = {}
    for polygon in mesh.polygons:
        if polygon.material_index not in skin_indices:
            continue
        for loop in polygon.loop_indices:
            i = mesh.loops[loop].vertex_index
            if basis[i].co.z < 1.52:
                continue
            skin_loops.setdefault(i, loop)
    # The scan has many tiny skin-labelled holes inside the hair cap. Their
    # edges are not hairlines: feathering each one creates bald spots. Select
    # the connected outer perimeter after welding coincident UV-seam vertices.
    edge_kinds = defaultdict(set)
    for polygon in mesh.polygons:
        kind = ('hair' if polygon.material_index == original_index else
                'skin' if polygon.material_index in skin_indices else None)
        if kind is None:
            continue
        for a, b in polygon.edge_keys:
            if min(basis[a].co.z, basis[b].co.z) < 1.52:
                continue
            edge = tuple(sorted((key(a), key(b))))
            if edge[0] != edge[1]:
                edge_kinds[edge].add(kind)
    graph = defaultdict(set)
    for (a, b), kinds in edge_kinds.items():
        if len(kinds) == 2:
            graph[a].add(b); graph[b].add(a)
    remaining, components = set(graph), []
    while remaining:
        seed = remaining.pop()
        component, stack = {seed}, [seed]
        while stack:
            for point in graph[stack.pop()]:
                if point in remaining:
                    remaining.remove(point); component.add(point); stack.append(point)
        components.append(component)
    outer = max(components, key=len)
    assert max(p[0] for p in outer)-min(p[0] for p in outer) > .15
    boundary = {point: Vector(point) for point in outer}
    assert len(boundary) > 50, len(boundary)
    edge_tree = KDTree(len(boundary))
    for index, point in enumerate(boundary.values()):
        edge_tree.insert(point, index)
    edge_tree.balance()
    hair_tree = KDTree(len(hair_vertices))
    for index, i in enumerate(hair_vertices):
        hair_tree.insert(basis[i].co, index)
    hair_tree.balance()
    # Sample beyond the baked dark transition. Carry both albedo UVs and the
    # existing photo blend weight, rather than substituting a uniform skin tint.
    clean = [i for i in skin_loops
             if i not in hair_vertices and hair_tree.find(basis[i].co)[2] >= .007]
    assert len(clean) > 100, len(clean)
    clean_tree = KDTree(len(clean))
    for i in clean:
        clean_tree.insert(basis[i].co, i)
    clean_tree.balance()
    coverage = mesh.attributes.new('V548_HairCoverage', 'FLOAT', 'POINT')
    photo_weight = mesh.attributes.new('V548_ScalpPhotoBlend', 'FLOAT', 'POINT')
    previous_weight = mesh.attributes['V377_PhotoSkinBlend']
    clean_uv = mesh.uv_layers.new(name='V548_CleanScalp')
    clean_photo_uv = mesh.uv_layers.new(name='V548_CleanPhotoScalp')
    original_uv = mesh.uv_layers['UVMap']
    photo_uv = mesh.uv_layers['V377_FacePhotoProjection']
    sources, distances, feathered = {}, [], 0
    part_vertices, part_sample_distances = 0, []
    for i in hair_vertices:
        point = basis[i].co
        distance = edge_tree.find(point)[2]
        _, source, source_distance = clean_tree.find(point)
        t = min(1., distance / width) if source_distance < .025 else 1.
        value = t*t*(3.-2.*t)
        # The interior part needs clean scalp as well as a gap between guides.
        # Keep the visible lane 3 mm wide and feather it to the hair cap over
        # 2.5 mm on either side; the wider root exclusion allows curl overlap.
        if point.z > 1.720 and -.105 < point.y < .065:
            part = .040 + .13 * (point.y + .070)
            lane = min(1., max(0., (abs(point.x-part)-.0015)/.0025))
            end_fade = min(1., (point.y+.105)/.005, (.065-point.y)/.005)
            part_coverage = 1. - end_fade * (1. - lane*lane*(3.-2.*lane))
            value = min(value, part_coverage)
            if part_coverage < 1.:
                part_vertices += 1
                part_sample_distances.append(source_distance)
        coverage.data[i].value = value
        sources[i] = skin_loops[source]
        photo_weight.data[i].value = previous_weight.data[source].value
        if t < 1.:
            distances.append(source_distance)
            feathered += 1
    for polygon in hair_faces:
        for loop in polygon.loop_indices:
            source = sources.get(mesh.loops[loop].vertex_index)
            if source is not None:
                clean_uv.data[loop].uv = original_uv.data[source].uv
                clean_photo_uv.data[loop].uv = photo_uv.data[source].uv
    material = skin.copy()
    material.name = 'V548_FEATHERED_HAIRLINE'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    source_uv = nodes.new('ShaderNodeUVMap')
    source_uv.uv_map = clean_uv.name
    links.new(source_uv.outputs['UV'], nodes['Image Texture'].inputs['Vector'])
    fitted_photo = nodes['V377_FittedPhotoAlbedo']
    fitted_uv = nodes.new('ShaderNodeUVMap')
    fitted_uv.uv_map = clean_photo_uv.name
    links.new(fitted_uv.outputs['UV'], fitted_photo.inputs['Vector'])
    for node in nodes:
        if node.type == 'ATTRIBUTE' and node.attribute_name == 'V377_PhotoSkinBlend':
            node.attribute_name = photo_weight.name
    output_node = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    skin_surface = output_node.inputs['Surface'].links[0].from_socket
    hair_shader = nodes.new('ShaderNodeBsdfPrincipled')
    original_shader = next(n for n in original.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for name in ('Base Color', 'Roughness', 'Specular IOR Level'):
        hair_shader.inputs[name].default_value = original_shader.inputs[name].default_value
    hair_attribute = nodes.new('ShaderNodeAttribute')
    hair_attribute.attribute_name = coverage.name
    mix = nodes.new('ShaderNodeMixShader')
    links.new(hair_attribute.outputs['Fac'], mix.inputs[0])
    links.new(skin_surface, mix.inputs[1])
    links.new(hair_shader.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs[0], output_node.inputs['Surface'])
    mesh.materials.append(material)
    for polygon in hair_faces:
        polygon.material_index = len(mesh.materials)-1
    mesh.update()
    report = {'original_material': original.name, 'trial_material': material.name,
              'hair_faces': len(hair_faces), 'boundary_points': len(boundary),
              'ignored_internal_boundary_components': len(components)-1,
              'feather_width_m': width, 'feathered_vertices': feathered,
              'clean_skin_candidates': len(clean),
              'maximum_skin_sample_distance_m': max(distances),
              'part_vertices': part_vertices,
              'part_skin_sample_maximum_distance_m': max(part_sample_distances, default=0.),
              'geometry_changed': False, 'status': 'TRIAL_REQUIRES_VISUAL_REVIEW'}
    (Path(output) / 'hairline-report.json').write_text(json.dumps(report, indent=2))
    return report
