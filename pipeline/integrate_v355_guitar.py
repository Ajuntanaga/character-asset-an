"""Append the preserved guitar hierarchy to the repaired Tripo/CloudRig body."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v355_guitar_fit'
out.mkdir(exist_ok=True)
source = root / 'production_v342_graphite_contour_guitar/Character_An_graphite_contour_guitar_v342.blend'
scene = bpy.data.scenes['V354_CLOUDRIG_DRIVERS']
bpy.context.window.scene = scene
scene.frame_set(1)
rig = scene.objects['V354_CLOUDRIG_CONTROLS']
if rig.animation_data and rig.animation_data.action:
    rig.animation_data.action.use_fake_user = True
    rig.animation_data.action = None
if bpy.data.objects.get('V206_GUITAR_ROOT'):
    raise RuntimeError('A guitar is already loaded; do not append another')
with bpy.data.libraries.load(str(source), link=False) as (src, dst):
    dst.objects = [name for name in src.objects
                   if name.startswith('V206_') or name == 'V318_BODY_REVEAL']
guitar = bpy.data.objects['V206_GUITAR_ROOT']
members = set(guitar.children_recursive) | {guitar}
imported = []
for obj in dst.objects:
    if obj in members:
        scene.collection.objects.link(obj)
        imported.append(obj)
    elif obj and obj.users == 0:
        bpy.data.objects.remove(obj)
if len(imported) < 20:
    raise RuntimeError('Incomplete guitar hierarchy')
for obj in scene.objects:
    if obj.name.startswith('V354_'):
        obj.name = obj.name.replace('V354_', 'V355_', 1)
scene.name = 'V355_CHARACTER_GUITAR_FIT'
scene['quality_status'] = 'Preserved V342 guitar appended; arm and finger contact not yet fitted'
bpy.context.view_layer.update()


def bounds(obj):
    values = [obj.matrix_world @ Vector(point) for point in obj.bound_box]
    return {'min': [min(point[i] for point in values) for i in range(3)],
            'max': [max(point[i] for point in values) for i in range(3)]}


report = {
    'source': str(source), 'imported_objects': [obj.name for obj in imported],
    'guitar_matrix_world': [list(row) for row in guitar.matrix_world],
    'guitar_constraints': [{'name': c.name, 'type': c.type,
                            'target': getattr(getattr(c, 'target', None), 'name', None)}
                           for c in guitar.constraints],
    'bounds': {name: bounds(scene.objects[name]) for name in
               ('V355_TRIPO_CHARACTER_BODY_BOUND', 'V206_BODY_CORE',
                'V206_FRETBOARD', 'V206_NECK')},
    'arm_controls': {bone.name: {'head': list(rig.matrix_world @ bone.head),
                               'tail': list(rig.matrix_world @ bone.tail),
                               'matrix': [list(row) for row in bone.matrix],
                               'rotation_mode': bone.rotation_mode}
                     for bone in rig.pose.bones if bone.name.startswith(
                         ('IK-', 'FK-', 'DEF-')) and any(
                             key in bone.name for key in ('Shoulder.', 'UpperArm.', 'Forearm.', 'Hand.', 'Elbow'))},
    'rig_properties': {key: properties for key, properties in rig.pose.bones['Properties'].items()
                       if isinstance(properties, (str, int, float, bool))},
}
camera = scene.camera
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x, scene.render.resolution_y = 900, 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.15
for label, position in (('front', (.15, -4, 1.05)), ('side', (3.5, -2.5, 1.10))):
    camera.location = position
    camera.rotation_euler = (Vector((.15, -.02, .96)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(out / f'v355_initial_{label}.png')
    bpy.ops.render.render(write_still=True)
camera.location = (.15, -4, 1.05)
camera.rotation_euler = (Vector((.15, -.02, .96)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
(out / 'guitar_integration.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Character_An_guitar_initial_fit_v355.blend'), compress=True)
print(json.dumps({key: value for key, value in report.items() if key not in ('arm_controls', 'rig_properties', 'imported_objects')}))
