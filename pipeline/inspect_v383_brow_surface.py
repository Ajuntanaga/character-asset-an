"""Export a small brow sampling field for a surface-attached fiber overlay."""
from pathlib import Path
import json
import random
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v383_face_detail'
OUT.mkdir(exist_ok=True)
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mesh = body.data
basis = mesh.shape_keys.key_blocks['Basis']
mesh.calc_loop_triangles()
triangles = [t for t in mesh.loop_triangles
             if all(1.650<basis.data[i].co.z<1.695 and basis.data[i].co.y<-.025
                    for i in t.vertices)]
coords = [v.co.copy() for v in basis.data]
bvh = BVHTree.FromPolygons(coords,[list(t.vertices) for t in triangles],all_triangles=True)
material = bpy.data.materials['V377_REFERENCE_PHOTO_SKIN']
image = material.node_tree.nodes['V377_FittedPhotoAlbedo'].image
pixels = np.empty(len(image.pixels),np.float32)
image.pixels.foreach_get(pixels)
width,height = image.size
pixels = pixels.reshape((height,width,4))[::4,::4,:3].copy()
height,width,_ = pixels.shape
uvs = mesh.uv_layers['V377_FacePhotoProjection']
weight = mesh.attributes['V377_PhotoSkinBlend']
rng = random.Random(383)
records = []
for side,lo,hi in [('L',.010,.071),('R',-.068,-.008)]:
    for _ in range(5000):
        x,z = rng.uniform(lo,hi),rng.uniform(1.656,1.686)
        hit,normal,index,_ = bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
        if hit is None or normal.y>-.15:
            continue
        tri = triangles[index]
        ids = list(tri.vertices)
        bary = barycentric_transform(hit,*[coords[i] for i in ids],
                                     Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        photo_weight = sum(weight.data[i].value*w for i,w in zip(ids,bary))
        if photo_weight<.25:
            continue
        uv = sum((uvs.data[li].uv*w for li,w in zip(tri.loops,bary)),Vector((0,0)))
        col = pixels[min(height-1,max(0,round(uv.y*(height-1)))),
                     min(width-1,max(0,round(uv.x*(width-1))))]
        lum = float(np.dot(col,(.2126,.7152,.0722)))
        records.append({'side':side,'point':list(hit),'normal':list(normal),
                        'ids':ids,'bary':list(bary),'luma':lum,'photo_weight':photo_weight})
report = {'materials':[m.name for m in mesh.materials],'source_image':image.name,
          'per_side':{}}
for side in ('L','R'):
    rows = [r for r in records if r['side']==side]
    lum = np.asarray([r['luma'] for r in rows])
    cutoff = float(np.quantile(lum,.20))
    dark = [r['point'] for r in rows if r['luma']<cutoff]
    report['per_side'][side] = {'samples':len(rows),
                              'luma_quantiles':np.quantile(lum,[.05,.10,.20,.35,.50,.80]).tolist(),
                              'dark_centroid':np.mean(dark,axis=0).tolist(),
                              'dark_bounds':[np.min(dark,axis=0).tolist(),np.max(dark,axis=0).tolist()]}
(OUT/'brow_samples.json').write_text(json.dumps(records,separators=(',',':')))
(OUT/'brow_sample_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
