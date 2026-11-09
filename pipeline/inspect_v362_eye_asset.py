"""Append the local free eye into an unlinked inspection collection."""
import bpy, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v362_face_anatomy'
with bpy.data.libraries.load(str(ROOT/'third_party/blenderkit_free/procedural_eye.blend'),link=False) as (src,dst):
    dst.objects=list(src.objects)
objects=[]
for obj in dst.objects:
    if obj is None: continue
    obj.name='V362_SOURCE_'+obj.name
    d={'name':obj.name,'type':obj.type,'parent':obj.parent.name if obj.parent else None,'matrix':list(map(list,obj.matrix_world)),'dimensions':list(obj.dimensions)}
    if obj.type=='MESH':
        d.update(vertices=len(obj.data.vertices),polygons=len(obj.data.polygons),bounds=[list(v) for v in obj.bound_box],materials=[m.name for m in obj.data.materials],modifiers=[(m.name,m.type) for m in obj.modifiers])
        d['shape_keys']=[(k.name,k.value) for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else []
    objects.append(d)
materials={}
def node_value(s):
    if not hasattr(s,'default_value'): return None
    v=s.default_value
    if isinstance(v,(str,int,float,bool)) or v is None: return v
    try: return list(v)
    except TypeError: return str(v)
for obj in dst.objects:
    if obj is None or obj.type!='MESH': continue
    for m in obj.data.materials:
        if not m or not m.use_nodes: continue
        materials[m.name]=[{'name':n.name,'label':n.label,'type':n.bl_idname,'group':n.node_tree.name if n.type=='GROUP' else None,'inputs':{i.name:node_value(i) for i in n.inputs if not i.is_linked}} for n in m.node_tree.nodes]
data={'objects':objects,'materials':materials,'version':bpy.app.version_string}
(OUT/'eye_asset_structure.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data))
