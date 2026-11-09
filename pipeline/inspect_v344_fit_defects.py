import bpy, json, numpy as np
from pathlib import Path
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
obj=bpy.data.objects['V344_SOURCE_Unisex Denim Shirt Design']
n=len(obj.data.vertices);xyz=np.empty(n*3,dtype=np.float32)
obj.data.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
parents=np.arange(n,dtype=np.int32)
def find(x):
    while parents[x]!=x:
        parents[x]=parents[parents[x]];x=parents[x]
    return x
for e in obj.data.edges:
    a,b=map(find,e.vertices)
    if a!=b: parents[b]=a
labels=np.array([find(i) for i in range(n)])
roots,inv,counts=np.unique(labels,return_inverse=True,return_counts=True)
panels=[]
for k,count in enumerate(counts):
    if count<500: continue
    pts=xyz[inv==k]
    panels.append({'root':int(roots[k]),'count':int(count),'min':pts.min(0).tolist(),'max':pts.max(0).tolist(),'mean':pts.mean(0).tolist(),'mean_abs_x':float(abs(pts[:,0]).mean())})
np.savez(ROOT/'production_v344_free_asset_wardrobe/panels.npz',xyz=xyz,labels=labels)
fitted=bpy.data.objects['V344_FITTED_CHARCOAL_DENIM_JACKET']
slots=[{'link':s.link,'name':s.material.name,'nodes':[(n.name,n.type) for n in s.material.node_tree.nodes]} for s in fitted.material_slots]
report={'panels':panels,'slots':slots}
(ROOT/'production_v344_free_asset_wardrobe/fit_defects.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
