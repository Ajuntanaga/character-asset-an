import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v362_face_anatomy'
group=bpy.data.node_groups['Eyeball']
report=[]
for n in group.nodes:
    if n.type in {'BSDF_PRINCIPLED','BSDF_GLOSSY','BSDF_GLASS','GROUP','TEX_COORD','TEX_IMAGE','OUTPUT_MATERIAL','BUMP'}:
        report.append({'name':n.name,'type':n.bl_idname,'group':n.node_tree.name if n.type=='GROUP' else None,'inputs':{i.name:(str(i.default_value) if hasattr(i,'default_value') else None) for i in n.inputs if not i.is_linked}})
eye=bpy.data.objects['V362_EYE.L']
report.append({'uv_layers':[u.name for u in eye.data.uv_layers],'materials':[m.name for m in eye.data.materials]})
(OUT/'eye_shader_diagnosis.json').write_text(json.dumps(report,indent=2))
for side in ('L','R'):bpy.data.objects['V362_CORNEA.'+side].hide_render=True
scene=bpy.context.scene;scene.render.filepath=str(OUT/'v362_without_cornea.png')
bpy.ops.render.render(write_still=True)
for side in ('L','R'):bpy.data.objects['V362_CORNEA.'+side].hide_render=False
print(json.dumps(report))
