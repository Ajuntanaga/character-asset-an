"""Reference proportion candidate through existing IK controls, preserving contact anchors."""
from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v426_hand_proportions';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'production_v425_shirt_scale' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
body=bpy.data.objects['V416_BODY_CLEAN_JOIN']
old=bpy.data.materials['V391_CONTINUOUS_COLLAR'];mat=old.copy();mat.name='V426_Scaled_Collar'
tex=mat.node_tree.nodes['V385_BotanicalPrint']
tex.inputs['Vector'].links[0].from_node.inputs['Scale'].default_value=1/.72
for s in body.material_slots:
 if s.material==old:s.material=mat
report={}
for side in ('L','R'):
 ctrl=rig.pose.bones['IK-Hand.'+side]
 digits=('Middle',) if side=='L' else ('Index','Thumb')
 def anchor():
  return sum((rig.pose.bones[f'DEF-Finger_{d}3.{side}'].tail.copy() for d in digits),Vector())/len(digits)
 before=anchor();original={'matrix_basis':[list(v) for v in ctrl.matrix_basis],'scale':list(ctrl.scale)}
 ctrl.scale*=1.18
 rig.update_tag();bpy.context.view_layer.update()
 delta=before-anchor()
 matrix=ctrl.matrix.copy();matrix.translation+=delta;ctrl.matrix=matrix
 rig.update_tag();bpy.context.view_layer.update()
 error=(anchor()-before).length
 assert error<.00001,error
 report[side]={'before':original,'factor':1.18,'anchor_digits':digits,'anchor_error_m':error,'wrist_shift_m':list(delta)}
report['rig_drivers']=len(rig.animation_data.drivers)
report['status']='Candidate requiring visual and surface-contact checks; bone anchors alone do not prove fingertip contact'
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_hand_proportions_v426.blend'))
print(json.dumps(report))
