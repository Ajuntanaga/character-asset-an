"""Run with Shapely to prepare a valid constant-width maple-cap contour."""
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
ROOT=Path(__file__).resolve().parents[1]
xy=json.loads((ROOT/'production_v356_reference_guitar/wood_outline.json').read_text())['points']
p=Polygon(xy)
assert p.is_valid
q=p.buffer(-.0025,join_style='round')
assert q.geom_type=='Polygon' and q.is_valid
ring=orient(q,sign=1).exterior
points=[list(ring.interpolate(i*ring.length/800).coords[0]) for i in range(800)]
assert Polygon(points).is_valid
(ROOT/'production_v400_maple_perimeter/inset_outline.json').write_text(json.dumps(points))
