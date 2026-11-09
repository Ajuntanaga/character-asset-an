import json
from pathlib import Path
import bpy
from mathutils import Vector

out = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v355_guitar_fit')
root = bpy.data.objects['V206_GUITAR_ROOT']
rig = bpy.data.objects['V355_CLOUDRIG_CONTROLS']
inv = root.matrix_world.inverted()
records = []
for obj in root.children_recursive:
    vertices = [inv @ obj.matrix_world @ Vector(v) for v in obj.bound_box]
    item = dict(name=obj.name, type=obj.type, hidden=obj.hide_render,
                location=list(obj.location), scale=list(obj.scale),
                matrix_local=[list(row) for row in inv @ obj.matrix_world],
                bounds=[list(min(v[i] for v in vertices) for i in range(3)),
                        list(max(v[i] for v in vertices) for i in range(3))],
                materials=[m.name if m else None for m in getattr(obj.data, 'materials', [])])
    if obj.type == 'CURVE':
        item['splines'] = [[list(p.co) for p in s.points] for s in obj.data.splines]
    records.append(item)
arms = {}
for b in rig.pose.bones:
    if any(term in b.name for term in ('Hand.', 'UpperArm.', 'Forearm.', 'Elbow', 'POLE-Arm', 'IK-M-Arm')):
        arms[b.name] = dict(head=list(b.head), tail=list(b.tail),
                            parent=b.parent.name if b.parent else None,
                            matrix=[list(row) for row in b.matrix],
                            constraints=[dict(type=c.type, name=c.name,
                                              target=getattr(getattr(c, 'target', None), 'name', None),
                                              subtarget=getattr(c, 'subtarget', None),
                                              pole=getattr(c, 'pole_subtarget', None)) for c in b.constraints])
report = dict(guitar=records, arms=arms)
(out/'guitar_local_inspection.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'objects':len(records),'arm_bones':len(arms),'drivers':len(rig.animation_data.drivers),
                  'key_bounds': {r['name']:r['bounds'] for r in records if r['name'] in (
                      'V206_FRETBOARD','V206_NECK','V206_BODY_CORE','V206_FIGURED_TOP','V206_PICKUP_NECK',
                      'V206_PICKUP_BRIDGE','V206_REAR_ELECTRONICS_COVER')},
                  'pole_bones':[b.name for b in rig.pose.bones if 'POLE' in b.name and 'Arm' in b.name]}))
