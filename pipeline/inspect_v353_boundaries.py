import bpy
import bmesh
import json
from pathlib import Path

out = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v353_cuff_repair')
body = bpy.data.objects['V352_TRIPO_CHARACTER_BODY_BOUND']
bm = bmesh.new()
bm.from_mesh(body.data)
bm.verts.ensure_lookup_table()
edges = {e for e in bm.edges if e.is_boundary and all(abs(v.co.x) > .23 and .83 < v.co.z < .96 for v in e.verts)}
components = []
while edges:
    todo = [edges.pop()]
    component = []
    while todo:
        edge = todo.pop()
        component.append(edge)
        for vertex in edge.verts:
            for adjacent in vertex.link_edges:
                if adjacent in edges:
                    edges.remove(adjacent)
                    todo.append(adjacent)
    vertices = {v for e in component for v in e.verts}
    components.append({'edges': len(component), 'vertices': len(vertices),
                       'min': [min(v.co[i] for v in vertices) for i in range(3)],
                       'max': [max(v.co[i] for v in vertices) for i in range(3)],
                       'closed': all(sum(e in component for e in v.link_edges) == 2 for v in vertices),
                       'indices': [v.index for v in vertices]})
bm.free()
components.sort(key=lambda x: -x['edges'])
(out / 'boundary_components.json').write_text(json.dumps(components, indent=2))
print(json.dumps([{k:v for k,v in c.items() if k != 'indices'} for c in components[:20]]))
