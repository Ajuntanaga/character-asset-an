from pathlib import Path
import bpy,json,numpy as np
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
collection=bpy.data.collections.get('V344_CC0_SOURCES')
if collection is None:
    collection=bpy.data.collections.new('V344_CC0_SOURCES')
    bpy.context.scene.collection.children.link(collection)
report=[]
for item in ('jeans','boots','shirt'):
    name='V344_CC0_SOURCE_'+item
    o=bpy.data.objects.get(name)
    if o is None:
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(ROOT/'third_party/charactercreator_cc0'/('clothing_'+item+'.glb')))
        created=set(bpy.data.objects)-before
        for ob in created:
            ob.name=name if ob.type=='MESH' else name+'_'+ob.name
            for c in list(ob.users_collection): c.objects.unlink(ob)
            collection.objects.link(ob)
            ob.hide_render=True;ob.hide_set(True)
        o=bpy.data.objects[name]
    bpy.context.view_layer.update()
    pts=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices])
    report.append({'name':o.name,'verts':len(pts),'min':pts.min(0).tolist(),'max':pts.max(0).tolist(),
      'materials':[m.name for m in o.data.materials], 'groups':len(o.vertex_groups),
      'shapekeys':len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0,
      'modifiers':[(m.name,m.type) for m in o.modifiers]})
    np.save(ROOT/'production_v344_free_asset_wardrobe'/('cc0_'+item+'_coords.npy'),pts)
o=bpy.data.objects['V344_FITTED_CHARCOAL_DENIM_JACKET']
for slot in o.material_slots:
    b=next(n for n in slot.material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    report.append({'material':slot.material.name,'inputs':{s.name:s.default_value if s.type=='VALUE' else list(s.default_value) for s in b.inputs if s.type in ('VALUE','RGBA')},'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in slot.material.node_tree.links]})
(ROOT/'production_v344_free_asset_wardrobe/cc0_import_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
