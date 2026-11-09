"""Retain the dense curl layout with fewer spline controls and old grooms unloaded."""
from pathlib import Path
import gc
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v382_clumped_curls'
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
obj = bpy.data.objects['V382B_CURL_GROOM']
old = obj.data
count = len(old.curves)
assert len(old.points) == count*48
assert (ROOT/'production_v381_facial_controls/Character_An_facial_controls_v381.blend').exists()
report = {'old_points':len(old.points),'strands':count,'removed_superseded_grooms':[]}

# Every earlier accepted groom is already preserved in the V381 checkpoint.
# The rejected V382 experiment also remains reproducible from its build script.
for name in ('V370_CURL_GROOM','V371_CURL_GROOM','V373_CURL_GROOM',
             'V375_CURL_GROOM','V376_CURL_GROOM','V382_CURL_GROOM'):
    stale = bpy.data.objects.get(name)
    if stale is None:
        continue
    assert stale.hide_render
    data = stale.data
    report['removed_superseded_grooms'].append({'name':name,'points':len(data.points)})
    bpy.data.objects.remove(stale,do_unlink=True)
    if data.users == 0:
        bpy.data.hair_curves.remove(data)

steps = 17
sample = np.linspace(0.,47.,steps,dtype=np.float32)
lo,hi = np.floor(sample).astype(int),np.ceil(sample).astype(int)
fraction = sample-lo
positions = np.empty((count,48,3),np.float32)
old.position_data.foreach_get('vector',positions.ravel())
resampled = (positions[:,lo,:]*(1-fraction)[None,:,None]
             +positions[:,hi,:]*fraction[None,:,None]).astype(np.float32)
del positions
radii = np.empty((count,48),np.float32)
old.attributes['radius'].data.foreach_get('value',radii.ravel())
new_radii = (radii[:,lo]*(1-fraction)[None,:]
             +radii[:,hi]*fraction[None,:]).astype(np.float32)
del radii
uv = np.empty((count,2),np.float32)
old.attributes['surface_uv_coordinate'].data.foreach_get('vector',uv.ravel())
curves = bpy.data.hair_curves.new('V382B_COMPACT_CURL_STRANDS')
curves.add_curves([steps]*count)
curves.set_types(type='CATMULL_ROM')
curves.position_data.foreach_set('vector',resampled.ravel())
curves.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',new_radii.ravel())
curves.attributes.new('surface_uv_coordinate','FLOAT2','CURVE').data.foreach_set('vector',uv.ravel())
curves.attributes.new('resolution','INT','CURVE').data.foreach_set('value',np.full(count,3,np.int32))
curves.surface = old.surface
curves.surface_uv_map = old.surface_uv_map
curves.surface_collision_distance = old.surface_collision_distance
for material in old.materials:
    curves.materials.append(material)
obj.data = curves
if old.users == 0:
    bpy.data.hair_curves.remove(old)
obj['V382B_compact_points_per_strand'] = steps
curves.update_tag()
bpy.context.scene.render.use_persistent_data = False
bpy.context.view_layer.update()
report['new_points'] = len(curves.points)
report['rig_drivers'] = len(rig.animation_data.drivers)
assert report['rig_drivers'] == 1957
(OUT/'groom_compaction_report.json').write_text(json.dumps(report,indent=2))
del resampled,new_radii,uv
gc.collect()
print(json.dumps(report))
