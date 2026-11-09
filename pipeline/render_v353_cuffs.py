"""Small one-thread Workbench deformation previews in the live MCP session."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v353_cuff_repair'
scene = bpy.data.scenes['V353_CLOUDRIG_CUFFS']
rig = scene.objects['V353_CLOUDRIG_CONTROLS']
camera = scene.camera
camera_state = camera.matrix_world.copy(), camera.data.type, camera.data.ortho_scale
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x, scene.render.resolution_y = 700, 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .245
paths = []
for frame, label in ((1, 'open'), (24, 'curl')):
    scene.frame_set(frame)
    for side, sign in (('L', 1), ('R', -1)):
        camera.location = (sign * 1.2, -.18, .875)
        camera.rotation_euler = (Vector((sign * .30, .01, .85)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'v353_cuff_{side}_{label}.png')
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)
scene.frame_set(1)
stress = {}
for side, sign in (('L', 1), ('R', -1)):
    control = rig.pose.bones.get('FK-Hand.' + side)
    if control is None:
        raise RuntimeError('Missing wrist FK control: ' + side)
    before_mode, before_matrix = control.rotation_mode, control.matrix_basis.copy()
    control.rotation_mode = 'XYZ'
    control.rotation_euler = (.35, .20 * sign, .12 * sign)
    bpy.context.view_layer.update()
    camera.location = (sign * 1.2, -.18, .875)
    camera.rotation_euler = (Vector((sign * .30, .01, .85)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(out / f'v353_cuff_{side}_wrist_bend.png')
    bpy.ops.render.render(write_still=True)
    paths.append(scene.render.filepath)
    stress[side] = list(control.rotation_euler)
    control.rotation_mode = before_mode
    control.matrix_basis = before_matrix
scene.frame_set(1)
camera.matrix_world, camera.data.type, camera.data.ortho_scale = camera_state
(out / 'preview_report.json').write_text(json.dumps({'engine': 'Workbench texture preview',
    'images': paths, 'wrist_test_rotation_radians': stress,
    'limits': 'Does not establish Cycles material quality or guitar contact'}, indent=2))
print(json.dumps({'images': paths, 'wrist_test': stress}))
