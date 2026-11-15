"""Reversible native-head neck skinning trial; run on the cloud groom checkpoint."""
from pathlib import Path
import json
import bpy

out = Path('results')
out.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.parent == rig and head.parent_type == 'BONE'
assert head.parent_bone == 'DEF-Head'
assert not any(m.type == 'ARMATURE' for m in head.modifiers)
deform_names = {bone.name for bone in rig.data.bones if bone.use_deform}
assert not ({group.name for group in head.vertex_groups} & deform_names), 'Existing deform weights require explicit migration'
keys = head.data.shape_keys
key_names = [key.name for key in keys.key_blocks]
assert len(key_names) == 52
# Binding in a posed rig would introduce a rest-pose offset. Refuse that case.
rest_errors = {}
for name in ('DEF-Neck', 'DEF-Head'):
    pose = rig.pose.bones[name]
    rest_errors[name] = max(abs(pose.matrix[i][j] - pose.bone.matrix_local[i][j])
                            for i in range(4) for j in range(4))
assert max(rest_errors.values()) < 2e-5, rest_errors
bpy.context.view_layer.update()
world = head.matrix_world.copy()

def evaluated_world():
    obj = head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    try:
        return [obj.matrix_world @ v.co for v in mesh.vertices]
    finally:
        obj.to_mesh_clear()

before = evaluated_world()
# Preserve all shape-key coordinates and drivers; only change attachment/weights.
head.parent_type = 'OBJECT'
head.parent_bone = ''
head.matrix_parent_inverse = rig.matrix_world.inverted()
head.matrix_world = world
neck = head.vertex_groups.get('DEF-Neck') or head.vertex_groups.new(name='DEF-Neck')
skull = head.vertex_groups.get('DEF-Head') or head.vertex_groups.new(name='DEF-Head')
counts = {'neck': 0, 'blend': 0, 'head': 0}
for vertex in head.data.vertices:
    z = (world @ keys.key_blocks['Basis'].data[vertex.index].co).z
    # Bottom opening remains neck-led; all facial tissue above the jaw stays head-led.
    t = max(0., min(1., (z - 1.480) / .055))
    w = t * t * (3. - 2. * t)
    neck.add([vertex.index], 1. - w, 'REPLACE')
    skull.add([vertex.index], w, 'REPLACE')
    counts['neck' if w == 0 else 'head' if w == 1 else 'blend'] += 1
modifier = head.modifiers.new('V755 neck-to-head skinning trial', 'ARMATURE')
modifier.object = rig
modifier.use_deform_preserve_volume = True
with bpy.context.temp_override(object=head, active_object=head):
    bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=0)
assert head.modifiers[0] == modifier
bpy.context.view_layer.update()
after = evaluated_world()
assert len(before) == len(after)
error = max((a - b).length for a, b in zip(before, after))
assert error < 5e-5, f'Neutral attachment shifted {error} m'
assert [key.name for key in keys.key_blocks] == key_names
assert all(counts.values()), counts
report = {'status': 'NEUTRAL_BIND_CHECKED_MOTION_AND_BODY_SEAM_UNREVIEWED',
          'neutral_max_displacement_m': error, 'rest_matrix_errors': rest_errors,
          'shape_keys': key_names, 'weight_counts': counts,
          'transition_world_z_m': [1.480, 1.535],
          'source': bpy.data.filepath,
          'limitations': ['Isolated native head; full-body seam not integrated',
                          'Head motion renders required before acceptance']}
(out / 'v755-neck-skinning-report.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out / 'V755_neck_skinning_trial.blend').resolve()), compress=True)
print(json.dumps(report))
