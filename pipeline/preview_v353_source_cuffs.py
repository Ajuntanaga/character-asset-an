"""Inspect the untouched cuff surface in the existing MCP Blender session."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v353_cuff_repair'
scene = bpy.context.scene
scene.frame_set(1)
body = scene.objects['V352_TRIPO_CHARACTER_BODY_BOUND']
source = bpy.data.objects.get('V353_ORIGINAL_CUFF_REFERENCE')
if source is None:
    with bpy.data.libraries.load(str(root / 'production_v350_tripo_cloudrig_body/Character_An_CloudRig_body_v350.blend'), link=False) as (src, dst):
        dst.objects = ['V350_TRIPO_CHARACTER_BODY_BOUND']
    source = dst.objects[0]
    source.name = 'V353_ORIGINAL_CUFF_REFERENCE'
    source.parent = None
    source.matrix_world = body.matrix_world
    source.modifiers.clear()
    source.data.materials.clear()
    for mat in body.data.materials:
        source.data.materials.append(mat)
    scene.collection.objects.link(source)

camera = scene.camera
state = {'matrix': camera.matrix_world.copy(), 'type': camera.data.type,
         'scale': camera.data.ortho_scale, 'engine': scene.render.engine,
         'x': scene.render.resolution_x, 'y': scene.render.resolution_y,
         'percentage': scene.render.resolution_percentage}
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = 700
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.show_specular_highlight = True
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .21
camera.location = (1.2, -.18, .89)
camera.rotation_euler = (Vector((.30, .01, .885)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
hands = [scene.objects['V352_ANATOMICAL_HAND.' + s] for s in ('L', 'R')]
try:
    source.hide_render = False
    source.hide_set(False)
    body.hide_render = True
    for hand in hands:
        hand.hide_render = True
    scene.render.filepath = str(out / 'v353_original_cuff_L.png')
    bpy.ops.render.render(write_still=True)
    source.hide_render = True
    source.hide_set(True)
    body.hide_render = False
    for hand in hands:
        hand.hide_render = False
    scene.render.filepath = str(out / 'v353_before_cuff_L.png')
    bpy.ops.render.render(write_still=True)
finally:
    source.hide_render = True
    source.hide_set(True)
    body.hide_render = False
    for hand in hands:
        hand.hide_render = False
    camera.matrix_world = state['matrix']
    camera.data.type = state['type']
    camera.data.ortho_scale = state['scale']
    scene.render.resolution_x, scene.render.resolution_y = state['x'], state['y']
    scene.render.resolution_percentage = state['percentage']
print(json.dumps({'source_vertices': len(source.data.vertices), 'source_faces': len(source.data.polygons),
                  'preview_paths': [str(out / x) for x in ('v353_original_cuff_L.png', 'v353_before_cuff_L.png')]}))
