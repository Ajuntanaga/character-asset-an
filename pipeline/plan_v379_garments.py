"""Classify the existing scan surface without changing its topology or UVs."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v379_fabric_eyes'
data = np.load(OUT/'body_material_samples.npz')
p, rgb = data['centers'], data['colors']
x, y, z = p.T
labels = np.zeros(len(p), dtype=np.int8)
# The scan is upright, arms down, in its Basis. The shirt front is bounded
# by the jacket opening; its curved hem also appears below the jacket.
heights = [.91, 1.0, 1.10, 1.20, 1.35, 1.40, 1.45, 1.50, 1.53]
left = np.interp(z, heights, [-.071, -.056, -.049, -.047, -.045, -.043, -.060, -.077, -.075])
right = np.interp(z, heights, [.080, .070, .058, .052, .047, .044, .065, .072, .070])
front_shirt = (x>left)&(x<right)&(z>.905)&(z<1.53)&(y<-.045)
hem_bottom = .848+.050*(abs(x)/.195)**2
shirt_hem = (z>hem_bottom)&(z<.908)&(abs(x)<.195)
shirt = front_shirt|shirt_hem
body_jacket = (z>.904)&(z<1.528)&((abs(x)<.218)|(z>.935))
# The upper collar is fabric, but the exposed central neck remains skin.
neck = (z>1.474)&(abs(x)<.065)&(y<.052)
jacket = body_jacket & ~shirt & ~neck
pants = (z>.238)&(z<.903)&(abs(x)<.225)&~shirt_hem
labels[pants] = 3
labels[jacket] = 1
labels[shirt & ~neck] = 2
# Keep the brass buttons and pocket pen on their unmodified texture.
button = (y<-.04)&(x>-.095)&(x<-.047)&(rgb[:,0]-rgb[:,2]>.065)
pen = (y<-.035)&(x>.117)&(x<.142)&(z>1.275)&(z<1.357)
labels[(button|pen)&(labels==1)] = 0
# Existing head/lid/hair materials are not wardrobe. The neck boundary
# intersects the original face slot, so the collar is explicitly recovered.
old = data['materials'][data['polyids']]
labels[(old!=0)&~((old==5)&(z<1.528)&~neck)] = 0
polygon_labels = np.zeros(len(data['materials']), dtype=np.int8)
polygon_labels[data['polyids']] = labels
np.save(OUT/'garment_polygon_labels.npy', polygon_labels)
(OUT/'garment_segmentation.json').write_text(json.dumps({
    'polygon_counts':{str(i):int((polygon_labels==i).sum()) for i in range(4)},
    'labels':{'0':'unchanged','1':'jacket','2':'shirt','3':'pants'}}, indent=2))

v = data['coords'][data['triangles']]
normal = np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0])
normal /= np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
canvas = Image.new('RGB',(1200,760),'#eeeeee')
draw = ImageDraw.Draw(canvas)
palette = np.array([[90,90,90],[45,85,160],[215,154,65],[110,65,125]])
for panel,(name,sign) in enumerate([('Front',-1),('Back',1)]):
    ids = np.flatnonzero((normal[:,1]*sign>.05)&(z>.22)&(z<1.54))
    ids = ids[np.argsort(-sign*y[ids])]
    draw.text((panel*600+20,12),name+' - blue jacket, gold shirt, purple pants',fill='black')
    for i in ids:
        px = int(panel*600+300+x[i]*760)
        py = int(730-(z[i]-.22)*510)
        draw.rectangle((px-1,py-1,px+1,py+1),fill=tuple(palette[labels[i]]))
canvas.save(OUT/'garment_segmentation.png')
print((OUT/'garment_segmentation.json').read_text())
