"""Read-only full-body collar geometry for fitting the replacement native head."""
import json
import os
from pathlib import Path

import bpy

body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
keys = body.data.shape_keys
basis = keys.key_blocks['Basis'].data if keys else body.data.vertices
world = [body.matrix_world @ v.co for v in basis]
# Includes the complete native lower-neck boundary and the surrounding collar.
selected = {i for i, p in enumerate(world)
            if abs(p.x) < .22 and 1.40 < p.z < 1.56}
faces = [p for p in body.data.polygons if any(i in selected for i in p.vertices)]
ids = sorted({i for p in faces for i in p.vertices})
report = {
    'status': 'JOIN_GEOMETRY_ONLY_NOT_INTEGRATED',
    'source': bpy.data.filepath,
    'body': body.name,
    'materials': [m.name if m else None for m in body.data.materials],
    'shape_keys': [k.name for k in keys.key_blocks] if keys else [],
    'vertices': [{'index': i, 'world_basis': list(world[i]),
                  'weights': {body.vertex_groups[g.group].name: g.weight
                              for g in body.data.vertices[i].groups}}
                 for i in ids],
    'faces': [{'index': p.index, 'vertices': list(p.vertices),
               'material': p.material_index} for p in faces],
    'rig_world': [list(row) for row in rig.matrix_world],
    'bones': [{'name': b.name,
               'rest': [list(row) for row in b.matrix_local],
               'pose': [list(row) for row in rig.pose.bones[b.name].matrix]}
              for b in rig.data.bones if 'neck' in b.name.lower()
              or 'head' in b.name.lower()],
}
assert faces and ids, 'No collar geometry in expected world-space region'
output = Path(globals().get('OUTPUT_DIR', os.environ.get('OUT_DIR', 'results')))
output.mkdir(parents=True, exist_ok=True)
(output / 'native-head-body-join.json').write_text(json.dumps(report, indent=2))
print('HEAD_JOIN_INVENTORY', len(ids), 'vertices', len(faces), 'faces')
