from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v399_oral_materials';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
report={}
for name,color,roughness in [('V363_ORAL_MUCOSA',(.12,.025,.027,1),.38),('V363_GUMS',(.22,.045,.05,1),.34),('V363_TONGUE',(.28,.065,.072,1),.38)]:
 mat=bpy.data.materials[name];shader=mat.node_tree.nodes.get('Principled BSDF')
 assert shader and not shader.inputs['Base Color'].is_linked
 report[name]={'before':list(shader.inputs['Base Color'].default_value),'after':color}
 shader.inputs['Base Color'].default_value=color
 shader.inputs['Roughness'].default_value=roughness
 shader.inputs['Subsurface Weight'].default_value=.08
 shader.inputs['Subsurface Scale'].default_value=.001
for control in ('JawOpen','Smile.L','Smile.R','Blink.L','Blink.R'):rig.pose.bones['Head'][control]=0.
rig.update_tag();bpy.context.view_layer.update()
(OUT/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_oral_materials_v399.blend'),compress=True)
print(json.dumps(report))
