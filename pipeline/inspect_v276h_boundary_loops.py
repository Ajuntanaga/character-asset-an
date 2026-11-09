import json
import bpy

head = bpy.data.objects["V276E_GEO-head_animation_realistic"]
usage = {tuple(sorted(edge.vertices)): 0 for edge in head.data.edges}
for polygon in head.data.polygons:
    vertices = polygon.vertices
    for index, first in enumerate(vertices):
        key = tuple(sorted((first, vertices[(index + 1) % len(vertices)])))
        usage[key] = usage.get(key, 0) + 1
boundary = {vertex for edge, count in usage.items() if count == 1 for vertex in edge}
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = head.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
records = {}
try:
    for side, cx in (("L", 0.035), ("R", -0.035)):
        points = [
            evaluated.matrix_world @ mesh.vertices[index].co
            for index in boundary
            if abs((evaluated.matrix_world @ mesh.vertices[index].co).x - cx) < 0.035
            and 1.62 < (evaluated.matrix_world @ mesh.vertices[index].co).z < 1.73
            and (evaluated.matrix_world @ mesh.vertices[index].co).y < -0.08
        ]
        orbital = [
            evaluated.matrix_world @ vertex.co
            for vertex in mesh.vertices
            if abs((evaluated.matrix_world @ vertex.co).x - cx) < 0.032
            and 1.63 < (evaluated.matrix_world @ vertex.co).z < 1.72
            and (evaluated.matrix_world @ vertex.co).y < -0.09
        ]
        frontmost = sorted(orbital, key=lambda point: point.y)[:40]
        records[side] = {
            "boundary_count": len(points),
            "orbital_count": len(orbital),
            "frontmost": [[round(p.x, 6), round(p.y, 6), round(p.z, 6)] for p in frontmost],
            "orbital_z": [min(p.z for p in orbital), max(p.z for p in orbital)],
        }
finally:
    evaluated.to_mesh_clear()
print("V276H_BOUNDARY_LOOPS=" + json.dumps(records, sort_keys=True))
