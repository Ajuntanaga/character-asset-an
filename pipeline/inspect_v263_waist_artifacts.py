import bpy, json
from mathutils import Vector

rows=[]
for obj in bpy.context.scene.objects:
    if obj.type not in {"MESH","CURVE"}: continue
    corners=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    lo=[min(c[i] for c in corners) for i in range(3)]; hi=[max(c[i] for c in corners) for i in range(3)]
    if lo[2] < 1.0 and hi[2] > .82 and (hi[0]-lo[0]) > .35:
        rows.append({"name":obj.name,"type":obj.type,"min":[round(v,4) for v in lo],"max":[round(v,4) for v in hi],"hide_render":obj.hide_render})
print("V263_WAIST_ARTIFACTS="+json.dumps(rows,sort_keys=True))
