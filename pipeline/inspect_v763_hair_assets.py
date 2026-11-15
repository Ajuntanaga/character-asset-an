"""Inventory licensed donor grooms without evaluating or changing the full rig."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

label = sys.argv[sys.argv.index('--') + 1]
out = Path('results/hair-assets')
out.mkdir(parents=True, exist_ok=True)

def value(item):
    if isinstance(item, (str, float, int, bool)) or item is None:
        return item
    if isinstance(item, bpy.types.ID):
        return {'id': item.name, 'type': item.bl_rna.identifier}
    try:
        return list(item)
    except TypeError:
        return str(item)

objects = []
for obj in bpy.data.objects:
    if obj.type not in {'MESH', 'CURVES', 'CURVE', 'ARMATURE', 'CAMERA'}:
        continue
    row = {'name': obj.name, 'type': obj.type, 'data': obj.data.name,
           'parent': obj.parent.name if obj.parent else None,
           'matrix_world': [list(r) for r in obj.matrix_world],
           'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport,
           'collections': [c.name for c in obj.users_collection],
           'modifiers': []}
    if obj.type in {'MESH', 'CURVES', 'CURVE'}:
        corners = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
        row['bounds'] = [[min(p[i] for p in corners) for i in range(3)],
                         [max(p[i] for p in corners) for i in range(3)]]
        row['materials'] = [m.name if m else None for m in obj.data.materials]
    if obj.type == 'MESH':
        row['vertices'] = len(obj.data.vertices)
        row['uv_maps'] = [u.name for u in obj.data.uv_layers]
        row['particle_systems'] = [
            {'name': p.name, 'settings': p.settings.name,
             'type': p.settings.type, 'count': p.settings.count,
             'child_nbr': p.settings.child_percent,
             'rendered_child_nbr': p.settings.rendered_child_count}
            for p in obj.particle_systems]
    elif obj.type == 'CURVES':
        row.update(curves=len(obj.data.curves), points=len(obj.data.points),
                   surface=obj.data.surface.name if obj.data.surface else None,
                   surface_uv_map=obj.data.surface_uv_map,
                   attributes=[{'name': a.name, 'type': a.data_type, 'domain': a.domain}
                               for a in obj.data.attributes])
    elif obj.type == 'ARMATURE':
        row['head_bones'] = {b.name: {'head': list(obj.matrix_world @ b.head_local),
                                     'tail': list(obj.matrix_world @ b.tail_local)}
                             for b in obj.data.bones
                             if any(s in b.name.lower() for s in ('head', 'jaw', 'eye'))}
    for mod in obj.modifiers:
        m = {'name': mod.name, 'type': mod.type,
             'show_render': mod.show_render, 'show_viewport': mod.show_viewport}
        if mod.type == 'NODES' and mod.node_group:
            m['node_group'] = mod.node_group.name
            # Some legacy node modifiers have no IDProperty storage after versioning.
            try:
                keys = list(mod.keys())
            except TypeError:
                keys = []
            m['values'] = {k: value(mod[k]) for k in keys if not k.endswith('_attribute_name')}
            m['interface'] = [
                {'name': s.name, 'identifier': s.identifier, 'in_out': s.in_out}
                for s in mod.node_group.interface.items_tree if s.item_type == 'SOCKET']
        if mod.type == 'ARMATURE':
            m['object'] = mod.object.name if mod.object else None
        row['modifiers'].append(m)
    objects.append(row)

texts = {t.name: t.as_string()[:20000] for t in bpy.data.texts
         if any(w in t.name.lower() for w in ('license', 'readme', 'copyright', 'info'))}
report = {'label': label, 'filepath': bpy.data.filepath,
          'objects': objects, 'texts': texts,
          'scenes': [{'name': s.name, 'camera': s.camera.name if s.camera else None,
                      'frame': s.frame_current} for s in bpy.data.scenes],
          'images': [{'name': i.name, 'path': i.filepath, 'packed': bool(i.packed_file)}
                     for i in bpy.data.images]}
(out / f'{label}-inventory.json').write_text(json.dumps(report, indent=2))
print('HAIR_ASSET_INVENTORY', label, len(objects), flush=True)
