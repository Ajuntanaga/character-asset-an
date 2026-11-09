"""Bounded diagnostic of lid geometry and stray sclera pixels."""
import bpy, json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
out = root / 'production_v364_face_deformation'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
saved = {p: head[p] for p in ('Blink.L', 'Blink.R', 'JawOpen')}
camera = scene.camera
camera.location = (0, -1.4, 1.646)
camera.rotation_euler = (Vector((0, 0, 1.646))-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.ortho_scale = .19
scene.render.resolution_x = 800
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
report = {'file': bpy.data.filepath, 'lids': {}, 'lights': {}, 'tongue': {}}
for side in ('L', 'R'):
    ob = bpy.data.objects['V362_LIDS.'+side]
    report['lids'][side] = {
        key.name: [[list(key.data[j*64+i].co) for j in range(8)] for i in (0, 16, 32, 48)]
        for key in ob.data.shape_keys.key_blocks
    }
    report['lids'][side]['matrix'] = list(map(list, ob.matrix_world))
for ob in scene.objects:
    if ob.type == 'LIGHT' and not ob.hide_render:
        report['lights'][ob.name] = {'energy': ob.data.energy, 'location': list(ob.location)}
tongue = bpy.data.objects['V363_DENTAL_TONGUE']
report['tongue'] = {'material_indices': list(set(p.material_index for p in tongue.data.polygons)),
                    'materials': [m.name for m in tongue.data.materials]}
try:
    head['JawOpen'] = head['Blink.L'] = head['Blink.R'] = 0.
    rig.update_tag()
    for side in ('L', 'R'):
        bpy.data.objects['V362_EYE.'+side].hide_render = True
    bpy.context.view_layer.update()
    scene.render.filepath = str(out/'v364_diagnostic_without_globes.png')
    bpy.ops.render.render(write_still=True)
    for side in ('L', 'R'):
        bpy.data.objects['V362_EYE.'+side].hide_render = False
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (.55, .55, .55)
    head['Blink.L'] = head['Blink.R'] = 1.
    rig.update_tag()
    bpy.context.view_layer.update()
    scene.render.filepath = str(out/'v364_diagnostic_closed_clay.png')
    bpy.ops.render.render(write_still=True)
finally:
    for p, value in saved.items():
        head[p] = value
    for side in ('L', 'R'):
        bpy.data.objects['V362_EYE.'+side].hide_render = False
    scene.render.engine = 'BLENDER_EEVEE'
    rig.update_tag()
    bpy.context.view_layer.update()
    (out/'diagnosis.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'status': 'diagnosed', 'file': report['file'], 'tongue': report['tongue']}))
