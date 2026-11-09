"""Trace the photographed wooden silhouette, excluding neck and bridge tuners."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import CubicSpline
from scipy.ndimage import distance_transform_edt

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v356_reference_guitar'
OUT.mkdir(exist_ok=True)
# Pixel coordinates in the supplied 1479 x 2000 front product photograph.
# The covered bridge recess is interpolated between its visible wooden edges.
knots = np.array([
    (577,500),(533,535),(473,549),(419,535),(373,513),(324,474),
    (281,428),(247,370),(219,309),(201,249),(191,211),(182,199),
    (167,204),(153,221),(141,254),(134,288),(132,329),(132,369),
    (141,415),(154,456),(183,531),(214,602),(245,678),(269,749),
    (289,823),(301,892),(301,930),(297,967),(283,1024),(264,1085),
    (226,1163),(185,1239),(143,1324),(110,1394),(91,1450),(85,1490),
    (85,1532),(91,1579),(109,1625),(132,1666),(167,1723),(205,1778),
    (239,1824),(270,1855),(295,1888),(319,1909),(350,1923),(381,1931),
    (412,1930),(443,1924),(466,1910),(481,1894),(492,1874),(498,1853),
    (504,1825),(513,1800),(526,1784),(566,1770),(660,1749),(771,1705),
    (870,1660),(903,1652),(932,1663),(947,1690),(973,1728),(997,1734),
    (1025,1716),(1073,1659),(1134,1603),(1207,1556),(1289,1522),
    (1381,1493),(1406,1471),(1406,1444),(1378,1400),(1315,1340),
    (1248,1252),(1205,1163),(1184,1078),(1178,1005),(1186,962),
    (1198,916),(1220,871),(1243,828),(1265,785),(1284,748),(1290,714),
    (1277,691),(1248,678),(1215,686),(1169,714),(1110,750),(1050,780),
    (996,792),(948,785),(912,766),(882,735),
    (872,690),(857,630),(837,566),(790,520),(715,500),(640,500),
    (577,500),
], dtype=float)
distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(knots,axis=0),axis=1))]
curve = CubicSpline(distance, knots, bc_type='periodic')
pixels = curve(np.linspace(0,distance[-1],800,endpoint=False))
# One isotropic scale, calibrated to body width and the existing string fan.
scale = .330 / np.ptp(pixels[:,0])
points = np.c_[.563 + (pixels[:,1]-887)*scale, (pixels[:,0]-730)*scale]
record = dict(source='references/props/strandberg/strandberg_full_product.jpg',
              image_size=[1479,2000], knots_px=knots.tolist(), points=points.tolist(),
              meters_per_pixel=scale, neck_end_pixel_y=887,
              note='Single smooth wooden outline; bridge and neck are separate geometry; local Y increases toward treble side')
(OUT/'wood_outline.json').write_text(json.dumps(record,indent=2))
# Distance to the actual silhouette gives a burst that follows both cutaways.
lo,hi=points.min(axis=0)-.006,points.max(axis=0)+.006
resolution=1024
uv=(points-lo)/(hi-lo)
mask=Image.new('L',(resolution,resolution))
ImageDraw.Draw(mask).polygon([tuple(v) for v in uv*(resolution-1)],fill=255)
inside=np.array(mask)>0
dist=distance_transform_edt(inside,sampling=((hi-lo)[1]/resolution,(hi-lo)[0]/resolution))
burst=np.clip(dist/.029,0,1)
Image.fromarray(np.uint8(burst*255)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(OUT/'wood_edge_distance.png')
(OUT/'wood_uv.json').write_text(json.dumps(dict(lo=lo.tolist(),hi=hi.tolist())))
print(json.dumps(dict(points=len(points),width_m=float(np.ptp(points[:,1])),
                      length_m=float(np.ptp(points[:,0])),bounds=[lo.tolist(),hi.tolist()])))
