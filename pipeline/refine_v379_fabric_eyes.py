"""Refine the current eye asset and give the scan distinct cloth materials."""
from pathlib import Path
import json
import math
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v379_fabric_eyes'
scene = bpy.context.scene
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
mesh = body.data
assert not body.get('V379_fabric_eyes_applied')
assert len(rig.animation_data.drivers) == 1957
labels = np.load(OUT/'garment_polygon_labels.npy')
assert len(labels) == len(mesh.polygons)

backup = {'eyes':{},'corneas':{},'lights':{},'old_materials':[p.material_index for p in mesh.polygons]}
for side in ('L','R'):
    eye = bpy.data.objects['V374_EYE.'+side]
    keys = eye.data.shape_keys.key_blocks
    backup['eyes'][side] = {k.name:[list(v.co) for v in k.data] for k in keys}
    basis = [v.co.copy() for v in keys[0].data]
    for i,p in enumerate(basis):
        if p.z < .005:
            continue
        r = math.hypot(p.x,p.y)
        t = min(1.,max(0.,(r-.0045)/.0045))
        factor = .78+.22*t*t*(3-2*t)
        for key in keys:
            key.data[i].co.x *= factor
            key.data[i].co.y *= factor
    eye.data.update()
    cornea = bpy.data.objects['V374_CORNEA.'+side]
    backup['corneas'][side] = [list(v.co) for v in cornea.data.vertices]
    for v in cornea.data.vertices:
        v.co.x *= .78
        v.co.y *= .78
    cornea.data.update()
for obj in scene.objects:
    if obj.type == 'LIGHT' and 'FILL' in obj.name:
        backup['lights'][obj.name] = {'visible_glossy':obj.visible_glossy}
        obj.visible_glossy = False

materials = {}
for label,name,tint,roughness,sheen in [
    (1,'V379_DARK_COTTON_JACKET',(.36,.375,.38,1.),.85,.055),
    (2,'V379_MUTED_PATTERN_SHIRT',(.65,.52,.37,1.),.76,.035),
    (3,'V379_DARK_COTTON_PANTS',(.40,.415,.42,1.),.86,.045),
]:
    mat = mesh.materials[0].copy()
    mat.name = name
    nodes, links = mat.node_tree.nodes,mat.node_tree.links
    shader = nodes['Principled BSDF']
    old_color = shader.inputs['Base Color'].links[0].from_socket
    multiply = nodes.new('ShaderNodeMixRGB')
    multiply.name = 'V379_ReferenceFabricColor'
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = 1.
    multiply.inputs[2].default_value = tint
    links.new(old_color,multiply.inputs[1])
    links.new(multiply.outputs[0],shader.inputs['Base Color'])
    for socket,value in [('Roughness',roughness),('Specular IOR Level',.20),
                         ('Metallic',0.),('Coat Weight',0.),('Sheen Weight',sheen),
                         ('Sheen Roughness',.8),('Diffuse Roughness',.25),
                         ('Subsurface Weight',0.)]:
        for link in list(shader.inputs[socket].links):
            links.remove(link)
        shader.inputs[socket].default_value = value
    position = nodes.new('ShaderNodeAttribute')
    position.attribute_name = 'V372_RestPosition'
    noise = nodes.new('ShaderNodeTexNoise')
    noise.name = 'V379_FabricMicrofibers'
    noise.inputs['Scale'].default_value = 2400.
    noise.inputs['Detail'].default_value = 2.
    noise.inputs['Roughness'].default_value = .65
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .16
    bump.inputs['Distance'].default_value = .000045
    links.new(position.outputs['Vector'],noise.inputs['Vector'])
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    mesh.materials.append(mat)
    materials[label] = len(mesh.materials)-1
    attr = mesh.attributes.new('V379_'+['','Jacket','Shirt','Pants'][label], 'FLOAT','FACE')
    attr.data.foreach_set('value',(labels==label).astype(np.float32))
for polygon,label in zip(mesh.polygons,labels):
    if label:
        polygon.material_index = materials[int(label)]
mesh.update()
body['V379_fabric_eyes_applied'] = True
rig.update_tag()
bpy.context.view_layer.update()
assert len(rig.animation_data.drivers) == 1957
(OUT/'before_v379.json').write_text(json.dumps(backup))
report = {'garment_polygons':{str(k):int((labels==k).sum()) for k in materials},
          'iris_radius_multiplier':.78,'rig_drivers':len(rig.animation_data.drivers),
          'fill_glossy_visibility':False}
(OUT/'fabric_eyes_report.json').write_text(json.dumps(report,indent=2))
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.render.resolution_percentage = 100
scene.cycles.samples = 48
scene.render.resolution_x,scene.render.resolution_y = 800,1000
scene.camera.data.ortho_scale = 1.38
scene.camera.location = (0,-2.4,1.23)
scene.camera.rotation_euler = (Vector((0,0,1.23))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v379_fabric_eyes_upper_body.png')
bpy.ops.render.render(write_still=True)
scene.render.resolution_x = scene.render.resolution_y = 800
scene.camera.data.ortho_scale = .37
scene.camera.location = (0,-1.4,1.66)
scene.camera.rotation_euler = (Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v379_face_front.png')
bpy.ops.render.render(write_still=True)
scene['V379_STATUS'] = 'DARK_FABRIC_AND_EYE_PROPORTIONS_REVIEW_REQUIRED'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_fabric_eyes_v379.blend'),compress=True)
print(json.dumps(report))
