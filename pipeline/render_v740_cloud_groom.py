"""Cloud scalp-groom review with a neutral head material; not a skin or likeness render."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

OUT = Path('results/renders')
OUT.mkdir(parents=True, exist_ok=True)
names = ['V740_NATIVE_FACE', 'V737_GAZE.L', 'V737_GAZE.R', 'V737_EYE.L', 'V737_EYE.R',
         'V738_CORNEA.L', 'V738_CORNEA.R', 'V739_ORAL_CAVITY', 'V737_DENTAL_UPPER',
         'V739_DENTAL_LOWER', 'V739_DENTAL_TONGUE', 'V740_NATIVE_CURLS',
         'V740_NATIVE_UNDERCOAT']
# The isolated checkpoint's external photo texture is intentionally not used.
head = bpy.data.objects['V740_NATIVE_FACE']
clay = bpy.data.materials.new('Cloud groom review neutral head')
clay.use_nodes = True
shader = clay.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.25, .25, .25, 1)
shader.inputs['Roughness'].default_value = .7
head.data.materials.clear()
head.data.materials.append(clay)
for polygon in head.data.polygons:
    polygon.material_index = 0
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head_ctrl = rig.pose.bones['Head']
source_scene = bpy.context.scene
production = bpy.data.filepath
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.scenes.get('V740_LIVE_PREVIEW') is None
assert all(name in bpy.data.objects for name in names)
scene = bpy.data.scenes.new('V740_LIVE_PREVIEW')
visibility, created, results, saved_props = {}, [], [], {}
world = None
target = Vector((0, -.015, 1.640))

def add(name, data):
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    created.append((obj, data))
    return obj

def aim(obj):
    obj.rotation_euler = (target-obj.location).to_track_quat('-Z', 'Y').to_euler()

try:
    for name in names+[rig.name]:
        obj = bpy.data.objects[name]
        visibility[name] = (obj.hide_render, obj.hide_viewport)
        obj.hide_render = False
        obj.hide_viewport = False
        scene.collection.objects.link(obj)
        obj.hide_set(False, view_layer=scene.view_layers[0])
    for prop, value in globals().get('POSE', {}).items():
        saved_props[prop] = head_ctrl[prop]
        head_ctrl[prop] = value
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
    camera = add('V740_PREVIEW_CAMERA', bpy.data.cameras.new('V740_PREVIEW_CAMERA'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .35
    scene.camera = camera
    for label, location, power, size in [('KEY',(-.5,-.7,2.15),65,.14),('FILL',(.55,-.5,1.72),25,.30),('RIM',(.4,.45,2),45,.25)]:
        light = add('V740_PREVIEW_'+label, bpy.data.lights.new('V740_PREVIEW_'+label, 'AREA'))
        light.location = location
        light.data.energy = power
        light.data.shape = 'DISK'
        light.data.size = size
        aim(light)
    world = bpy.data.worlds.new('V740_PREVIEW_WORLD')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18,.18,.18,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    scene.world = world
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = globals().get('SAMPLES', 24)
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .08
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 512
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = -1.3
    for view in globals().get('VIEWS', ['front', 'three_quarter']):
        camera.location = {'front': (0,-.9,1.640), 'profile': (-.9,-.015,1.640),
                           'three_quarter': (-.65,-.665,1.640)}[view]
        aim(camera)
        scene.render.filepath = str(OUT/(globals().get('TAG','v740_neutral')+'_'+view+'.png'))
        bpy.ops.render.render(write_still=True, scene=scene.name)
        results.append(scene.render.filepath)
finally:
    for prop, value in saved_props.items():
        head_ctrl[prop] = value
    rig.update_tag(refresh={'OBJECT'})
    for name, flags in visibility.items():
        obj = bpy.data.objects[name]
        obj.hide_render, obj.hide_viewport = flags
    bpy.data.scenes.remove(scene)
    for obj, data in created:
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
    if world:
        bpy.data.worlds.remove(world)
    bpy.context.view_layer.update()
report = {'review_scope': 'scalp curl shape and coverage only; brows, beard and skin not evaluated', 'renders': results, 'restored_properties': saved_props,
          'rig_drivers': len(rig.animation_data.drivers),
          'production_unchanged': bpy.data.filepath == production and bpy.context.scene == source_scene}
(OUT.parent/(globals().get('TAG','v740_neutral')+'_render_report.json')).write_text(json.dumps(report, indent=2))
print(json.dumps(report))
