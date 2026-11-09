"""Replace hair-only underlay slot with explicit opaque rough fiber base."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v487_hair_underlay';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
body=bpy.data.objects['V416_BODY_CLEAN_JOIN'];old=body.data.materials[3]
assert old.name=='V371_DARK_HAIR_UNDERLAY'
(out/'original.json').write_text(json.dumps({'material':old.name,'groom_render':bpy.data.objects['V449_CURL_GROOM'].hide_render}))
m=bpy.data.materials.get('V487_MATTE_HAIR_UNDERLAY') or bpy.data.materials.new('V487_MATTE_HAIR_UNDERLAY');m.use_nodes=True
n=m.node_tree.nodes.get('Principled BSDF')
if 'Weight' in n.inputs:n.inputs['Weight'].default_value=1
n.inputs['Base Color'].default_value=(.009,.006,.004,1);n.inputs['Roughness'].default_value=.85;n.inputs['Specular IOR Level'].default_value=.12
body.data.materials[3]=m
bpy.data.objects['V449_CURL_GROOM'].hide_render=True
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v487_hair_underlay/isolated.png','resolution':[700,800],'samples':24,'scale':.46,'camera':[.1,-2,1.67],'target':[0,0,1.65]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
