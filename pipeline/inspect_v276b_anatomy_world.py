import json
import bpy

record = {"frame_before": bpy.context.scene.frame_current}
bpy.context.scene.frame_set(10)
for name in ("V216_EYE_L", "V216_EYE_R", "V276B_EYELID_L", "V276B_EYELID_R", "V276B_MOUTH_CAVITY"):
    obj = bpy.data.objects.get(name)
    if not obj:
        continue
    entry = {"origin": [round(v, 6) for v in obj.matrix_world.translation]}
    if obj.type == "MESH":
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        points = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
        entry["bounds"] = {
            "x": [round(min(p.x for p in points), 6), round(max(p.x for p in points), 6)],
            "y": [round(min(p.y for p in points), 6), round(max(p.y for p in points), 6)],
            "z": [round(min(p.z for p in points), 6), round(max(p.z for p in points), 6)],
        }
    record[name] = entry
print("V276B_ANATOMY_WORLD=" + json.dumps(record, sort_keys=True))
