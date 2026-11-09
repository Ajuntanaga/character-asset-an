"""Import the downloaded CC0 hair sources, hidden, for fitting inspection."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v346_free_hair_and_head'
OUT.mkdir(exist_ok=True)
collection = bpy.data.collections.get('V346_CC0_HAIR_SOURCES')
if collection is None:
    collection = bpy.data.collections.new('V346_CC0_HAIR_SOURCES')
    bpy.context.scene.collection.children.link(collection)
report = {}
for style in ('afro01', 'short04'):
    prefix = 'V346_SOURCE_' + style + '_'
    sources = [o for o in bpy.data.objects if o.name.startswith(prefix)]
    if not sources:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(ROOT / 'third_party/charactercreator_cc0' / ('hair_' + style + '.glb')))
        sources = list(set(bpy.data.objects) - before)
        for obj in sources:
            obj.name = prefix + obj.name
            for old_collection in list(obj.users_collection):
                old_collection.objects.unlink(obj)
            collection.objects.link(obj)
    items = []
    for obj in sources:
        obj.hide_render = True
        obj.hide_set(True)
        if obj.type != 'MESH':
            continue
        coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
        item = {'name': obj.name, 'vertices': len(coords),
                'bounds': [[min(v[i] for v in coords) for i in range(3)], [max(v[i] for v in coords) for i in range(3)]],
                'parent': obj.parent.name if obj.parent else None,
                'materials': []}
        for mat in obj.data.materials:
            item['materials'].append({'name': mat.name, 'nodes': [
                {'type': n.type, 'name': n.name, 'image': n.image.name if n.type == 'TEX_IMAGE' and n.image else None}
                for n in mat.node_tree.nodes]})
        items.append(item)
    report[style] = items
head = bpy.data.objects['V326_PHOTOREAL_FACEBUILDER_HEAD']
coords = [head.matrix_world @ v.co for v in head.data.vertices]
report['head'] = {'bounds': [[min(v[i] for v in coords) for i in range(3)], [max(v[i] for v in coords) for i in range(3)]],
                  'parent': head.parent.name if head.parent else None,
                  'modifiers': [(m.name, m.type) for m in head.modifiers]}
(OUT / 'source_inventory.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
