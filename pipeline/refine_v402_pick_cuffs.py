"""Remove skin-colored scan contamination on cuffs; shorten exposed plectrum."""
import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'production_v402_pick_wrist'
s=bpy.context.scene;assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
mat=bpy.data.materials.new('V402_Charcoal_Cotton_Cuff');mat.use_nodes=True
nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.026,.031,.033,1);bs.inputs['Roughness'].default_value=.82;bs.inputs['Sheen Weight'].default_value=.16
tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1900;tex.inputs['Detail'].default_value=2
coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.00012;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
report={'cuffs':{}}
for side in ['L','R']:
 o=bpy.data.objects['V357_CUFF_PATCH.'+side];report['cuffs'][side]={'previous_material':o.data.materials[0].name};o.data.materials[0]=mat
p=bpy.data.objects['V361_NYLON_PICK'];assert not p.get('V402_shortened')
fit=json.loads((R/'production_v361_pick_cuffs/final_fit_report.json').read_text())['pick'];center=Vector(fit['center_guitar']);direction=(Vector(fit['tip_guitar'])-center).normalized()
for v in p.data.vertices:
 along=(v.co-center).dot(direction)
 if along>0:v.co-=direction*along*(1-15/22)
p.data.update();p['V402_shortened']=True
report['pick']={'exposed_length_before_mm':22,'exposed_length_after_mm':15,'parent_bone':p.parent_bone};report['drivers']=len(r.animation_data.drivers)
(O/'report.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_pick_cuffs_v402.blend'),compress=True)
request=json.loads((R/'pipeline/render_preview_request.json').read_text());request['output']='production_v402_pick_wrist/v402_pick_close.png';(R/'pipeline/render_preview_request.json').write_text(json.dumps(request))
exec(compile((R/'pipeline/render_preview_job.py').read_text(),str(R/'pipeline/render_preview_job.py'),'exec'))
print(json.dumps(report))
