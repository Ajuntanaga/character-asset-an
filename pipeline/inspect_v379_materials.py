"""Export current surface data for garment segmentation and eye refinement."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v379_fabric_eyes'
OUT.mkdir(exist_ok=True)
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mesh = body.data
mesh.calc_loop_triangles()
coords = np.empty(len(mesh.vertices)*3, dtype=np.float32)
mesh.shape_keys.key_blocks[0].data.foreach_get('co', coords)
coords = coords.reshape(-1, 3)
triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
polyids = np.array([t.polygon_index for t in mesh.loop_triangles], dtype=np.int32)
uvs = np.empty(len(mesh.loops)*2, dtype=np.float32)
mesh.uv_layers['UVMap'].data.foreach_get('uv', uvs)
uvs = uvs.reshape(-1, 2)
tri_uvs = np.array([uvs[list(t.loops)] for t in mesh.loop_triangles], dtype=np.float32)
mat = mesh.materials[0]
image_node = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
tex = image_node.image
pixels = np.empty(len(tex.pixels), dtype=np.float32)
tex.pixels.foreach_get(pixels)
w, h = tex.size
pixels = pixels.reshape(h, w, 4)
uv_centers = tri_uvs.mean(axis=1)
xy = np.floor(uv_centers*np.array([w,h])).astype(np.int32)
xy[:,0] = np.clip(xy[:,0], 0, w-1)
xy[:,1] = np.clip(xy[:,1], 0, h-1)
colors = pixels[xy[:,1],xy[:,0],:3]
np.savez_compressed(OUT/'body_material_samples.npz', coords=coords, triangles=triangles,
                    polyids=polyids, colors=colors, centers=coords[triangles].mean(axis=1),
                    materials=np.array([p.material_index for p in mesh.polygons]))
eye = bpy.data.objects['V374_EYE.L']
group = next(n for n in eye.data.materials[0].node_tree.nodes if n.type == 'GROUP')
report = {'texture': {'name':tex.name, 'path':tex.filepath, 'size':list(tex.size)},
          'materials': [m.name for m in mesh.materials], 'lights':[], 'eye_group':[],
          'eye_mesh': {'basis':[list(v.co) for v in eye.data.shape_keys.key_blocks[0].data],
                       'uvs':[[loop.vertex_index,list(eye.data.uv_layers.active.data[loop.index].uv)]
                              for loop in eye.data.loops]}}
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        report['lights'].append({'name':obj.name,'visible_glossy':getattr(obj,'visible_glossy',None),
                                 'size':obj.data.size, 'energy':obj.data.energy,
                                 'specular_factor':obj.data.specular_factor})
for node in group.node_tree.nodes:
    if node.type in ('BSDF_PRINCIPLED','OUTPUT_MATERIAL','TEX_COORD','TEX_NOISE','GROUP_INPUT'):
        report['eye_group'].append({'name':node.name,'type':node.type,
          'inputs':{s.name: {'value': list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value,
                             'link':[(l.from_node.name,l.from_socket.name) for l in s.links]}
                     for s in node.inputs if hasattr(s,'default_value')},
          'outputs': {s.name:[(l.to_node.name,l.to_socket.name) for l in s.links] for s in node.outputs}})
(OUT/'materials_inspection.json').write_text(json.dumps(report,indent=2))
scene = bpy.context.scene
scene.render.resolution_x,scene.render.resolution_y = 800,1000
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.cycles.samples = 32
scene.camera.data.ortho_scale = 1.38
scene.camera.location = (0,-2.4,1.23)
scene.camera.rotation_euler = (Vector((0,0,1.23))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v379_before_upper_body.png')
bpy.ops.render.render(write_still=True)
print(json.dumps({'exported':str(OUT), 'triangles':len(triangles), 'texture':tex.name}))
