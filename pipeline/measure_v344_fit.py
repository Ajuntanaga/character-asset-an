import bpy, json, numpy as np
from pathlib import Path
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
source=bpy.data.objects['V344_SOURCE_Unisex Denim Shirt Design']
body=bpy.data.objects['V322_MB_MALE_BODY'];rig=bpy.data.objects['V322_MB_MALE_RIG']
def coords(o):
    a=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',a)
    a=a.reshape(-1,3);m=np.array(o.matrix_world);return a@m[:3,:3].T+m[:3,3]
a=coords(source);b=coords(body)
np.savez(ROOT/'production_v344_free_asset_wardrobe/fit_geometry.npz',garment=a,body=b)
rec={'pose_bones':[(p.name,list(rig.matrix_world@p.head),list(rig.matrix_world@p.tail),list(p.scale),list(p.rotation_quaternion))
    for p in rig.pose.bones if p.bone.use_deform and any(x in p.name for x in ('upper_arm','forearm','spine','hand'))],
    'garment_sections':[], 'body_sections':[], 'materials':[]}
for z in np.arange(.025,.63,.05):
    s=a[np.abs(a[:,2]-z)<.008]
    if len(s):rec['garment_sections'].append([round(float(z),3),np.quantile(s, [0,.1,.25,.5,.75,.9,1],axis=0).tolist()])
for z in np.arange(1.,1.65,.05):
    s=b[(np.abs(b[:,2]-z)<.015)&(np.abs(b[:,0])<.25)]
    if len(s):rec['body_sections'].append([round(float(z),3),s.min(axis=0).tolist(),s.max(axis=0).tolist()])
for m in source.data.materials:
    rec['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes], 'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]})
(ROOT/'production_v344_free_asset_wardrobe/fit_details.json').write_text(json.dumps(rec,indent=2))
print(json.dumps(rec))
