"""Stage a separate attributed donor hand, preserving the active character."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v519_source_anatomy'
path=root/'third_party/charmorph/v0.4.0-3/CharMorph-data/characters/antonia/char.blend'
with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=['cm_antonia']
source=dst.objects[0]
ids=[v.index for v in source.data.vertices if v.co.x>.57];mapping={v:i for i,v in enumerate(ids)}
polys=[p for p in source.data.polygons if all(i in mapping for i in p.vertices)]
mesh=bpy.data.meshes.new('V519_ANTONIA_DONOR_MESH');mesh.from_pydata([source.data.vertices[i].co[:] for i in ids],[],[[mapping[i] for i in p.vertices] for p in polys]);mesh.update()
for a,b in zip(mesh.polygons,polys):a.use_smooth=True;a.material_index=b.material_index
for layer in source.data.uv_layers:
 uv=mesh.uv_layers.new(name=layer.name)
 for a,b in zip(mesh.polygons,polys):
  for al,bl in zip(a.loop_indices,b.loop_indices):uv.data[al].uv=layer.data[bl].uv
obj=bpy.data.objects.new('V519_ANTONIA_HAND_DONOR',mesh)
obj['source_author']='Olaf Delgado-Friedrichs; phantom3D; MikeJ; DieTrying; Fenrissa and others'
obj['source_license']='CC-BY 3.0';obj['source_url']='https://sites.google.com/site/antoniapolygon/'
obj['status']='ANATOMICAL DONOR ONLY: requires reference fit, skinning and posed review'
mod=obj.modifiers.new('Subdivision','SUBSURF');mod.levels=2
blend=out/'Antonia_hand_donor_v519.blend';assert not blend.exists()
bpy.data.libraries.write(str(blend),{obj},fake_user=True)
(out/'antonia_vertex_map.json').write_text(json.dumps({'source':str(path),'original_vertex_ids':ids,'material_indices':[p.material_index for p in polys],'license':obj['source_license'],'attribution':obj['source_author']},indent=2))
bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
data=source.data;bpy.data.objects.remove(source,do_unlink=True)
if data.users==0:bpy.data.meshes.remove(data)
print(json.dumps({'donor':str(blend),'vertices':len(ids),'faces':len(polys),'character_unchanged':bpy.data.filepath,'drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)}))
