import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v414_sleeve_join';O.mkdir(exist_ok=True)
o=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND'];m=o.data
verts=[{'i':v.index,'co':list(v.co),'weights':[(o.vertex_groups[g.group].name,g.weight) for g in v.groups]} for v in m.vertices if -.36<v.co.x<-.23 and .93<v.co.z<.97]
(O/'body_join.json').write_text(json.dumps(verts))
print(json.dumps({'file':bpy.data.filepath,'vertices_near_join':len(verts),'modifiers':[(x.name,x.type) for x in o.modifiers],'matrix':[list(row) for row in o.matrix_world]}))
