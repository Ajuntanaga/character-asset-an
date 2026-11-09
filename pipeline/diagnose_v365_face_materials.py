"""Inspect the fitted face under physically occluding lighting."""
import bpy, json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
out = root/'production_v365_face_surface'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
report = {'world': {}, 'body_materials': {}, 'mouth_bounds': {}}
for material in body.data.materials:
    report['body_materials'][material.name] = {
        'nodes': [{'name': n.name, 'type': n.type} for n in material.node_tree.nodes],
        'links': [(l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name)
                  for l in material.node_tree.links]}
if scene.world and scene.world.use_nodes:
    report['world'] = {n.name: {s.name: str(s.default_value) for s in n.inputs if hasattr(s, 'default_value')}
                       for n in scene.world.node_tree.nodes}
for name in ('V363_DENTAL_UPPER', 'V363_DENTAL_LOWER', 'V363_DENTAL_TONGUE', 'V363_MOUTH_CAVITY'):
    ob = bpy.data.objects[name]
    coords = [ob.matrix_world @ v.co for v in ob.data.vertices]
    report['mouth_bounds'][name] = {
        'min': [min(v[k] for v in coords) for k in range(3)],
        'max': [max(v[k] for v in coords) for k in range(3)],
        'materials': [(m.name, [list(p.material_index for p in ob.data.polygons).count(i)])
                      for i, m in enumerate(ob.data.materials)]}
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 5
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 3
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = .40
scene.camera.location = (0, -1.4, 1.66)
scene.camera.rotation_euler = (Vector((0, 0, 1.66))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
head['Blink.L'] = head['Blink.R'] = 1.
head['JawOpen'] = .4
rig.update_tag()
bpy.context.view_layer.update()
(out/'material_diagnosis.json').write_text(json.dumps(report, indent=2))
scene.render.filepath = str(out/'v365_cycles_before_surface_repair.png')
bpy.ops.render.render(write_still=True)
head['Blink.L'] = head['Blink.R'] = head['JawOpen'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
print(json.dumps(report))
