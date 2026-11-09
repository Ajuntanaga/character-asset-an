"""Align closed eyelid skin to its existing closed margin in a reversible trial."""
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import bpy
from mathutils import Vector


def build(root, out):
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    assert not bpy.app.is_job_running('RENDER')
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert body.get('V544_eye_opening_applied')
    assert not body.get('V547_blink_alignment')
    keys = body.data.shape_keys.key_blocks
    material = list(body.data.materials).index(bpy.data.materials['V365_LID_SKIN'])
    counts = Counter(tuple(sorted(e)) for p in body.data.polygons for e in p.edge_keys)
    report, backup = {}, {}
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
    report['status'] = 'TRIAL_REQUIRES_RENDER_AND_DEFORMATION_REVIEW'
    report['rig_drivers'] = len(rig.animation_data.drivers)
    (out / 'blink-alignment-backup.json').write_text(json.dumps(backup))
    (out / 'blink-alignment-report.json').write_text(json.dumps(report, indent=2))
    return report
