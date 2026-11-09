import bpy, json, numpy as np
from pathlib import Path
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
report={'visible':[],'sections':{}}
for o in bpy.context.scene.objects:
    if o.type in {'MESH','CURVE','CURVES'} and not o.hide_render:
        report['visible'].append({'name':o.name,'materials':[m.name for m in o.data.materials]})
for name in ['V322_MB_MALE_BODY','V344_FITTED_CHARCOAL_DENIM_JACKET',
             'V345_TAILORED_CHARCOAL_DENIM_JACKET','V345_CC0_FITTED_FLORAL_SHIRT',
             'V326_PHOTOREAL_FACEBUILDER_HEAD']:
    o=bpy.data.objects[name]
    p=np.array([o.matrix_world@v.co for v in o.data.vertices])
    rows=[]
    for z in [1.03,1.15,1.25,1.35,1.40,1.45,1.5,1.55]:
        for x in [0.,.08,.14,.20]:
            a=p[(np.abs(p[:,2]-z)<.014)&(np.abs(p[:,0]-x)<.025)]
            if len(a): rows.append({'z':z,'x':x,'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist()})
    report['sections'][name]=rows
    np.save(ROOT/'production_v345_tailored_free_wardrobe'/f'{name}_coords.npy',p)
(ROOT/'production_v345_tailored_free_wardrobe/layers.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
