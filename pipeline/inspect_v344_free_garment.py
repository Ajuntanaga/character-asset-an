"""Append the licensed free source garment for fitting; emit bounded geometry data."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
stage = ROOT / 'production_v344_free_asset_wardrobe'
stage.mkdir(exist_ok=True)
asset = ROOT / 'third_party/blenderkit_free/unisex_denim_shirt_4k.blend'
collection = bpy.data.collections.get('V344_FREE_GARMENT_SOURCE')
if collection is None:
    collection = bpy.data.collections.new('V344_FREE_GARMENT_SOURCE')
    bpy.context.scene.collection.children.link(collection)
    with bpy.data.libraries.load(str(asset), link=False) as (src, dst):
        dst.objects = src.objects
    for obj in dst.objects:
        if obj:
            collection.objects.link(obj)
            obj['v344_source_name'] = obj.name
            obj.name = 'V344_SOURCE_' + obj.name
            obj.hide_render = True
            obj.hide_set(True)

def bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return [[min(v[i] for v in pts) for i in range(3)], [max(v[i] for v in pts) for i in range(3)]]

data = {'file': bpy.data.filepath, 'source_objects': [], 'body': {}, 'scene_objects': []}
for obj in collection.objects:
    data['source_objects'].append({'name': obj.name, 'type': obj.type,
        'bounds': bounds(obj), 'matrix_world': [list(r) for r in obj.matrix_world],
        'vertices': len(obj.data.vertices) if obj.type == 'MESH' else 0,
        'polygons': len(obj.data.polygons) if obj.type == 'MESH' else 0,
        'modifiers': [(m.name,m.type) for m in obj.modifiers],
        'materials': [m.name if m else None for m in obj.data.materials] if obj.type == 'MESH' else []})
body = bpy.data.objects['V322_MB_MALE_BODY']
rig = bpy.data.objects['V322_MB_MALE_RIG']
data['body'] = {'bounds':bounds(body), 'modifiers': [(m.name,m.type) for m in body.modifiers],
                'groups':[g.name for g in body.vertex_groups],
                'bones':[{ 'name': b.name, 'head':list(rig.matrix_world@b.head_local), 'tail':list(rig.matrix_world@b.tail_local)}
                         for b in rig.data.bones if b.use_deform]}
data['scene_objects'] = [{'name':o.name,'type':o.type,'visible':not o.hide_render,'bounds':bounds(o)}
                         for o in bpy.context.scene.objects if any(x in o.name.lower() for x in ['v325','jacket','neck','guitar','shirt'])]
data['asset_images']=[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)}
                       for i in bpy.data.images if 'denim' in i.name.lower() or 'dg100074' in i.name.lower()]
(stage/'source_geometry.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data))
