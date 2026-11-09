"""Match the approved shirt's readable botanical motif scale."""
from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
assert 'production_v424_rest_skin' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
body=bpy.data.objects['V416_BODY_CLEAN_JOIN']
assert 'V372_RestPosition' in body.data.attributes
old=bpy.data.materials['V379_MUTED_PATTERN_SHIRT']
mat=old.copy()
mat.name='V425_Reference_Scale_Botanical_Shirt'
tex=mat.node_tree.nodes['V385_BotanicalPrint']
scale=tex.inputs['Vector'].links[0].from_node
assert scale.type=='VECT_MATH' and scale.operation=='SCALE'
previous=scale.inputs['Scale'].default_value
scale.inputs['Scale'].default_value=1/.72
for slot in body.material_slots:
 if slot.material==old:slot.material=mat
out=ROOT/'production_v425_shirt_scale'
out.mkdir(exist_ok=True)
report={'previous_tile_m':1/previous,'new_tile_m':.72,'motif_linear_enlargement':3,'rig_drivers':len(rig.animation_data.drivers),'status':'Awaiting torso render comparison'}
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_shirt_scale_v425.blend'))
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
