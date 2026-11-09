from pathlib import Path
import bpy, json
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
report={'objects':[], 'bones':{}, 'materials':[]}
for ob in bpy.data.objects:
    if not (ob.name.startswith('V344_CC0_SOURCE') or ob.name=='V322_MB_MALE_RIG'):
        continue
    entry={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,
           'matrix':[list(row) for row in ob.matrix_world]}
    if ob.type=='MESH':
        entry.update(vertices=len(ob.data.vertices), materials=[m.name for m in ob.data.materials],
                     groups=[g.name for g in ob.vertex_groups])
    report['objects'].append(entry)
    if ob.type=='ARMATURE':
        report['bones'][ob.name]=[{'name':b.name,'head':list(ob.matrix_world@b.head_local),
          'tail':list(ob.matrix_world@b.tail_local),'deform':b.use_deform} for b in ob.data.bones
          if b.use_deform]
obj=bpy.data.objects['V344_FITTED_CHARCOAL_DENIM_JACKET']
for mat in obj.data.materials:
    nodes=[]
    for n in mat.node_tree.nodes:
        row={'name':n.name, 'type':n.type}
        if n.type=='TEX_IMAGE':
            row.update(image=n.image.name if n.image else None,
                       colorspace=n.image.colorspace_settings.name if n.image else None,
                       size=list(n.image.size) if n.image else None)
        if n.type=='NORMAL_MAP': row['strength']=n.inputs['Strength'].default_value
        if n.type=='HUE_SAT': row.update(value=n.inputs['Value'].default_value, saturation=n.inputs['Saturation'].default_value)
        nodes.append(row)
    report['materials'].append({'name':mat.name,'nodes':nodes})
(ROOT/'production_v344_free_asset_wardrobe/scene_asset_details.json').write_text(json.dumps(report,indent=2))
print('Saved scene_asset_details.json')
