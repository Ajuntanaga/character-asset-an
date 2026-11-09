"""Keep photo detail where alignment is clean; preserve original mouth and beard."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v377_photo_skin'
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mesh = body.data
assert not body.get('V377b_skin_mask_applied')

def smooth(t):
    t = min(1., max(0., t))
    return t*t*(3.-2.*t)

attribute = mesh.attributes['V377_PhotoSkinBlend']
for vertex in mesh.vertices:
    p = mesh.shape_keys.key_blocks['Basis'].data[vertex.index].co
    central = smooth((p.z-1.595)/.014)
    cheek = smooth((abs(p.x)-.044)/.017)*smooth((p.z-1.561)/.020)
    attribute.data[vertex.index].value *= max(central, cheek)*.88
body['V377b_skin_mask_applied'] = True
mesh.update()

def describe_tree(tree):
    result = []
    for node in tree.nodes:
        if node.type in {'BSDF_PRINCIPLED','BSDF_GLOSSY','BSDF_ANISOTROPIC',
                         'BSDF_TRANSPARENT','FRESNEL','MIX_SHADER','GROUP'}:
            inputs = {}
            for socket in node.inputs:
                if not hasattr(socket, 'default_value'):
                    continue
                value = socket.default_value
                try:
                    value = list(value)
                except TypeError:
                    pass
                inputs[socket.name] = {'value':value,'linked':socket.is_linked}
            result.append({'name':node.name,'type':node.type,'inputs':inputs})
            if node.type == 'GROUP':
                result.extend(describe_tree(node.node_tree))
    return result

report = {
    'eye_material':describe_tree(bpy.data.objects['V374_EYE.L'].data.materials[0].node_tree),
    'cornea_material':describe_tree(bpy.data.objects['V374_CORNEA.L'].data.materials[0].node_tree),
    'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,
               'location':list(o.location),'size':getattr(o.data,'size',None)}
              for o in bpy.context.scene.objects if o.type == 'LIGHT'],
    'uv_layers':[{'name':u.name,'render':u.active_render}
                 for u in mesh.uv_layers],
    'rig_drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers),
}
(OUT/'eye_shader_inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'mask_refined':True,'rig_drivers':report['rig_drivers'],
                  'uv_layers':report['uv_layers']}))
