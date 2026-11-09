"""Project the fitted photo donor onto the current rigged face, without replacing it."""
from pathlib import Path
import json
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v377_photo_skin'
OUT.mkdir(exist_ok=True)
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mesh = body.data
assert len(rig.animation_data.drivers) == 1957
assert not mesh.uv_layers.get('V377_FacePhotoProjection'), 'Already projected'
data = json.loads((ROOT/'production_v376_face_refinement/photo_donor_geometry.json').read_text())
# Eye centers, nose tip, mouth seam and chin define the local fit. The photo
# donor includes a long neck; a whole-object bounding box fit is unsuitable.
source_z = [-1.72,-.85,-.30,.0515203,.33,.52,.80,.94,1.3065]
target_z = [1.435,1.521,1.571,1.609121,1.645,1.670,1.709,1.732,1.795]
coords = [Vector((p[0]*.123+.0016,p[1]*.121+.00802,
                  float(np.interp(p[2],source_z,target_z)))) for p in data['vertices']]
bvh = BVHTree.FromPolygons(coords,data['triangles'],all_triangles=True)
uv_triangles = [[Vector((*uv,0.)) for uv in tri] for tri in data['triangle_uvs']]

def smooth(v):
    v = max(0.,min(1.,v))
    return v*v*(3.-2.*v)

uv_vertex = np.zeros((len(mesh.vertices),2),np.float32)
weights = np.zeros(len(mesh.vertices),np.float32)
counts = {'eligible':0,'projected':0,'missed':0,'distance_rejected':0,'normal_rejected':0}
distances = []
for v in mesh.vertices:
    p = mesh.shape_keys.key_blocks['Basis'].data[v.index].co
    weight = smooth((p.z-1.513)/.018)*smooth((1.733-p.z)/.018)
    weight *= smooth((.086-abs(p.x))/.016)*smooth((-.022-p.y)/.040)
    # Keep the current deformable eyelids and mouth interior. The transition
    # extends beyond the inserted lid annuli to avoid projecting baked eyes.
    for cx,cz in ((.038,1.645),(-.0355,1.645)):
        d = math.hypot((p.x-cx)/.022,(p.z-cz)/.012)
        weight *= smooth((d-1.)/.48)
    mouth = math.hypot((p.x+.0005)/.038,(p.z-1.571)/.012)
    weight *= smooth((mouth-.95)/.55)
    if weight <= .001:
        continue
    counts['eligible'] += 1
    hit,normal,index,_ = bvh.ray_cast(Vector((p.x,-.4,p.z)),Vector((0,1,0)))
    if hit is None:
        counts['missed'] += 1
        continue
    distance = abs(hit.y-p.y)
    if distance > .042:
        counts['distance_rejected'] += 1
        continue
    if normal.y > -.12:
        counts['normal_rejected'] += 1
        continue
    tri = data['triangles'][index]
    uv = barycentric_transform(hit,*[coords[i] for i in tri],*uv_triangles[index])
    uv_vertex[v.index] = uv.xy
    weights[v.index] = weight*.94
    counts['projected'] += 1
    distances.append(distance)

uv_layer = mesh.uv_layers.new(name='V377_FacePhotoProjection')
loop_vertices = np.empty(len(mesh.loops),np.int32)
mesh.loops.foreach_get('vertex_index',loop_vertices)
uv_layer.data.foreach_set('uv',uv_vertex[loop_vertices].ravel())
weight_attribute = mesh.attributes.new('V377_PhotoSkinBlend','FLOAT','POINT')
weight_attribute.data.foreach_set('value',weights)
previous = bpy.data.materials['V372_FACE_SKIN']
material = previous.copy()
material.name = 'V377_REFERENCE_PHOTO_SKIN'
mesh.materials.append(material)
material_index = len(mesh.materials)-1
previous_index = list(mesh.materials).index(previous)
for polygon in mesh.polygons:
    if polygon.material_index == previous_index:
        polygon.material_index = material_index
nodes,links = material.node_tree.nodes,material.node_tree.links
shader = nodes['Principled BSDF']
original = shader.inputs['Base Color'].links[0].from_socket
uv_node = nodes.new('ShaderNodeUVMap')
uv_node.uv_map = uv_layer.name
texture = nodes.new('ShaderNodeTexImage')
texture.name = 'V377_FittedPhotoAlbedo'
texture.image = bpy.data.images.load(str(ROOT/'production_v326_photoreal_facebuilder/textures/Character_An_photoreal_head_basecolor_v326.png'),check_existing=True)
texture.interpolation = 'Linear'
links.new(uv_node.outputs['UV'],texture.inputs['Vector'])
attribute = nodes.new('ShaderNodeAttribute')
attribute.attribute_name = weight_attribute.name
mix = nodes.new('ShaderNodeMixRGB')
mix.name = 'V377_PhotoSkinComposite'
links.new(attribute.outputs['Fac'],mix.inputs[0])
links.new(original,mix.inputs[1])
links.new(texture.outputs['Color'],mix.inputs[2])
links.new(mix.outputs[0],shader.inputs['Base Color'])
mesh.update()
bpy.context.view_layer.update()
report = {'projection':counts,'max_projection_distance_m':max(distances),
          'median_projection_distance_m':float(np.median(distances)),
          'source_z_landmarks':source_z,'target_z_landmarks':target_z,
          'rig_drivers':len(rig.animation_data.drivers),
          'body_shape_keys':list(mesh.shape_keys.key_blocks.keys()),
          'geometry_replaced':False}
(OUT/'photo_skin_report.json').write_text(json.dumps(report,indent=2))
scene = bpy.context.scene
scene.cycles.samples = 48
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.camera.data.ortho_scale = .37
scene.camera.location = (0,-1.4,1.66)
scene.camera.rotation_euler = (Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v377_photo_skin_front.png')
bpy.ops.render.render(write_still=True)
print(json.dumps(report))
