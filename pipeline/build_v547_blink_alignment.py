"""Align closed eyelid skin to its existing closed margin in a reversible trial."""
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def build(root, out):
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    assert not bpy.app.is_job_running('RENDER')
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert body.get('V544_eye_opening_applied')
    assert not body.get('V547_blink_alignment')
    # Re-open the reference aperture before computing the closed alignment and
    # corneal arc. Closed blink targets remain unchanged by this contour edit.
    from build_v544_reference_eyelids import build as reshape_aperture
    aperture = reshape_aperture(root, out, reopen=True)
    keys = body.data.shape_keys.key_blocks
    material = list(body.data.materials).index(bpy.data.materials['V365_LID_SKIN'])
    counts = Counter(tuple(sorted(e)) for p in body.data.polygons for e in p.edge_keys)
    report, backup, lid_vertices = {'aperture': aperture}, {}, {}
    for side, sign in (('L', 1), ('R', -1)):
        adjacent = defaultdict(set)
        for p in body.data.polygons:
            if p.material_index != material or keys['Basis'].data[p.vertices[0]].co.x * sign <= 0:
                continue
            for a, b in p.edge_keys:
                adjacent[a].add(b)
                adjacent[b].add(a)
        inner = {v for v, ns in adjacent.items() if any(counts[tuple(sorted((v, n)))] == 1 for n in ns)}
        assert len(inner) == 64
        distance = dict.fromkeys(inner, 0)
        queue = deque(inner)
        while queue:
            v = queue.popleft()
            for n in adjacent[v]:
                if n not in distance:
                    distance[n] = distance[v] + 1
                    queue.append(n)
        assert max(distance.values()) == 11
        lid_vertices[side] = list(distance)
        margin = bpy.data.objects['V369_LID_MARGIN.' + side].data.shape_keys.key_blocks
        centers = {k: [sum((margin[k].data[i*6+j].co for j in range(6)), Vector()) / 6
                       for i in range(64)] for k in ('Basis', 'Blink')}
        order = [min(inner, key=lambda v: (keys['Basis'].data[v].co - p).length_squared)
                 for p in centers['Basis']]
        assert len(set(order)) == 64
        key = keys['Blink.' + side]
        backup[side] = {str(v): list(key.data[v].co) for v in distance}
        shifts = []
        for i, start in enumerate(order):
            target = centers['Blink'][i] + Vector((0, .00007, 0))
            delta = target - key.data[start].co
            shifts.append(delta.length)
            v = start
            for row in range(11):
                key.data[v].co += delta * (1 - row / 11) ** 1.5
                children = [n for n in adjacent[v] if distance[n] == row + 1]
                assert len(children) == 1
                v = children[0]
        error = max((key.data[v].co - centers['Blink'][i] - Vector((0, .00007, 0))).length
                    for i, v in enumerate(order))
        assert error < 1e-6
        report[side] = {'maximum_correction_m': max(shifts), 'closed_margin_alignment_error_m': error}
    body['V547_blink_alignment'] = True
    from build_v544_reference_eyelids import rebuild_lashes
    rebuild_lashes(out)
    # The upper margin is a continuous tissue edge, not a continuous black
    # eyelash. Keep the individual lashes on their original dark material.
    upper_edge = bpy.data.materials['V367_WATERLINE'].copy()
    upper_edge.name = 'V554_UPPER_LID_TISSUE'
    upper_shader = upper_edge.node_tree.nodes['Principled BSDF']
    upper_shader.inputs['Roughness'].default_value = .45
    upper_shader.inputs['Coat Weight'].default_value = 0.
    margins = {}
    for side in ('L', 'R'):
        margin = bpy.data.objects['V369_LID_MARGIN.' + side]
        original = margin.data.materials[0]
        assert original.name == 'V367_LASH_LINE'
        margin.data.materials[0] = upper_edge
        margins[side] = {'previous_material': original.name,
                         'upper_edge_material': upper_edge.name}
    report['lid_margin_materials'] = margins
    # Linear shape interpolation cuts through the convex cornea. Add a smooth
    # outward arc whose influence is zero at both accepted endpoint shapes.
    dg = bpy.context.evaluated_depsgraph_get()
    for side in ('L', 'R'):
        cornea = bpy.data.objects['V374_CORNEA.' + side].evaluated_get(dg)
        mesh = cornea.to_mesh()
        world_vertices = [cornea.matrix_world @ v.co for v in mesh.vertices]
        faces = [list(p.vertices) for p in mesh.polygons]
        cornea.to_mesh_clear()
        corrections = {}
        for obj, closed_name, indices in (
            (body, 'Blink.' + side, lid_vertices[side]),
            (bpy.data.objects['V369_LID_MARGIN.' + side], 'Blink', None),
            (bpy.data.objects['V394_EYELASHES.' + side], 'Blink', None),
        ):
            # Objects share the head coordinate convention; transform the cornea
            # into each object's local space rather than assuming identical parents.
            inverse = obj.matrix_world.inverted()
            surface = BVHTree.FromPolygons([inverse @ v for v in world_vertices], faces, all_triangles=False)
            shape_keys = obj.data.shape_keys.key_blocks
            basis, closed = shape_keys['Basis'], shape_keys[closed_name]
            corrective = obj.shape_key_add(name='BlinkArc.' + side)
            maximum = 0.
            for i in indices if indices is not None else range(len(basis.data)):
                shift = 0.
                for step in range(1, 16):
                    t = step / 16
                    point = basis.data[i].co.lerp(closed.data[i].co, t)
                    hit, _, _, _ = surface.ray_cast(Vector((point.x, -.3, point.z)), Vector((0, 1, 0)), .5)
                    if hit is not None:
                        shift = max(shift, (point.y - hit.y + .0002) / (4*t*(1-t)))
                corrective.data[i].co.y -= shift
                maximum = max(maximum, shift)
            driver = corrective.driver_add('value').driver
            driver.type = 'SCRIPTED'
            variable = driver.variables.new()
            variable.name = 'blink'; variable.type = 'SINGLE_PROP'
            variable.targets[0].id = rig
            variable.targets[0].data_path = f'pose.bones["Head"]["Blink.{side}"]'
            driver.expression = '4*blink*(1-blink)'
            corrections[obj.name] = maximum
        report[side]['arc_maximum_displacement_m'] = corrections
    rig.update_tag()
    bpy.context.view_layer.update()
    # Historical V547 trial value. Actual source-mesh inspection established
    # that raising this control CONTRACTS the pupil; V558 corrects the combined
    # trial after this build. Keep this independent trial reproducible.
    report['pupils'] = {}
    for side in ('L', 'R'):
        dilation = bpy.data.objects['V374_EYE.' + side].data.shape_keys.key_blocks['Dilation']
        report['pupils'][side] = {'previous_dilation': dilation.value, 'trial_dilation': .60}
        dilation.value = .60
    # Retain the fitted photo UV and original material for rollback. Reduce
    # its baked lighting contribution only on the face's existing material.
    original_skin = bpy.data.materials['V377_REFERENCE_PHOTO_SKIN']
    original_slot = list(body.data.materials).index(original_skin)
    balanced_skin = original_skin.copy()
    balanced_skin.name = 'V549_REFERENCE_PHOTO_SKIN_BALANCED'
    nodes, links = balanced_skin.node_tree.nodes, balanced_skin.node_tree.links
    composite = nodes['V377_PhotoSkinComposite']
    weight = composite.inputs[0].links[0].from_socket
    gain = nodes.new('ShaderNodeMath')
    gain.name = 'V549_PhotoSkinBlendGain'
    gain.operation = 'MULTIPLY'; gain.inputs[1].default_value = .65
    links.new(weight, gain.inputs[0]); links.new(gain.outputs[0], composite.inputs[0])
    body.data.materials.append(balanced_skin)
    affected = 0
    for polygon in body.data.polygons:
        if polygon.material_index == original_slot:
            polygon.material_index = len(body.data.materials)-1
            affected += 1
    report['photo_skin'] = {'material': balanced_skin.name, 'photo_blend_gain': .65,
                            'affected_faces': affected, 'original_material': original_skin.name}
    report['status'] = 'TRIAL_REQUIRES_RENDER_AND_DEFORMATION_REVIEW'
    report['rig_drivers'] = len(rig.animation_data.drivers)
    (out / 'blink-alignment-backup.json').write_text(json.dumps(backup))
    (out / 'blink-alignment-report.json').write_text(json.dumps(report, indent=2))
    return report
