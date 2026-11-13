"""Cloud-only matched clay comparison; never writes the source checkpoint."""
import json
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

out = Path('results')
out.mkdir(exist_ok=True)
scene = bpy.data.scenes['V739_NATIVE_FACE_INSPECTION']
face = bpy.data.objects['V739_NATIVE_FACE']
mesh = face.data
before_coordinates = [tuple(v.co) for v in mesh.vertices]
before_faces = [tuple(p.vertices) for p in mesh.polygons]
for obj in scene.objects:
    if obj.type == 'MESH':
        obj.hide_render = obj != face
for modifier in face.modifiers:
    modifier.show_render = False
clay = bpy.data.materials.new('Diagnostic neutral clay')
clay.use_nodes = True
shader = clay.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.35, .35, .35, 1)
shader.inputs['Roughness'].default_value = .7
scene.view_layers[0].material_override = clay
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.resolution_x = 512
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

def inspect():
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    records = []
    for f in bm.faces:
        center = face.matrix_world @ f.calc_center_median()
        if abs(center.x) < .05 and center.z < 1.56 and center.y < 0:
            neighbors = {n for e in f.edges for n in e.link_faces if n != f}
            records.append({'face': f.index, 'area': f.calc_area(),
                            'min_neighbor_dot': min((f.normal.dot(n.normal) for n in neighbors), default=1)})
    bm.free()
    return records

def render(tag):
    for view, location in [('front', (0, -.9, 1.635)), ('threequarter', (.55, -.8, 1.635))]:
        scene.camera.location = location
        scene.camera.rotation_euler = (Vector((0, -.015, 1.635)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'{tag}_{view}.png')
        bpy.ops.render.render(write_still=True, scene=scene.name)

report = {'before': inspect(), 'modifiers_disabled': True}
render('before')
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
mesh.update()
assert before_coordinates == [tuple(v.co) for v in mesh.vertices], 'Coordinates changed'
report['changed_face_winding_count'] = sum(a != tuple(p.vertices) for a, p in zip(before_faces, mesh.polygons))
report['after'] = inspect()
report['coordinates_unchanged'] = True
(out / 'normals-report.json').write_text(json.dumps(report, indent=2))
render('after')
