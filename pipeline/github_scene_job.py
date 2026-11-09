"""Read a release scene and emit a bounded CPU preview and scene report."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('check', 'preview', 'review', 'build-review', 'hand-build', 'groom-build'), default='check')
parser.add_argument('--output', default='results')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
if args.mode == 'build-review':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_v544_reference_revision import build
    build(out)
if args.mode == 'hand-build':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_v545_fretting_hand import build
    build(out)
if args.mode == 'groom-build':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_v546_coherent_groom import build
    build(out)
scene = bpy.context.scene
rig = bpy.data.objects.get('V357_CLOUDRIG_CONTROLS')
if rig is None or rig.animation_data is None:
    raise RuntimeError('Main character rig missing')
count = len(rig.animation_data.drivers)
if count != 1957:
    raise RuntimeError(f'Unexpected main rig driver count: {count}')
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).is_file()]
if missing or bpy.data.libraries:
    raise RuntimeError(f'Scene is not self-contained: missing={missing}, linked={len(bpy.data.libraries)}')
report = {'blender': bpy.app.version_string, 'scene': Path(bpy.data.filepath).name,
          'objects': len(scene.objects), 'main_drivers': count, 'missing_images': missing,
          'mode': args.mode, 'quality_status': 'WORK_IN_PROGRESS_NOT_ACCEPTED'}
(out / 'scene-report.json').write_text(json.dumps(report, indent=2))
if args.mode in ('preview', 'review', 'build-review', 'hand-build', 'groom-build'):
    review = args.mode in ('review', 'build-review', 'hand-build', 'groom-build')
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32 if review else 8
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.render.use_simplify = True
    scene.render.simplify_subdivision_render = 1
    scene.render.simplify_child_particles_render = 0.1
    size = 768 if review else 512
    scene.render.resolution_x = size; scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    camera = scene.camera
    if camera is None:
        raise RuntimeError('Scene camera missing')
    shots = [('instrument', (-.00624775, -.645, .74370837),
              (-.10234958, -.27, 1.0314399), .42)]
    if review:
        pick = bpy.data.objects['V361_NYLON_PICK']
        center = sum((pick.matrix_world @ v.co for v in pick.data.vertices), Vector()) / len(pick.data.vertices)
        shots.extend([
            ('pick-grip', center + Vector((.13, -.2, .04)), center, .16),
            ('character', (.35, -3.5, 1.3), (0, 0, .94), 2.12),
            ('portrait', (.30, -2, 1.7), (0, 0, 1.64), .58),
        ])
    if args.mode == 'hand-build':
        shots = [s for s in shots if s[0] != 'portrait']
        fit = json.loads((out / 'hand-fit-report.json').read_text())
        center = sum((Vector(fit['contacts'][d]['target_world']) for d in ('Index', 'Middle', 'Ring', 'Pinky')), Vector()) / 4
        guitar = bpy.data.objects['V206_GUITAR_ROOT'].matrix_world
        offset = guitar.to_3x3()
        context_shots = shots
        if fit['status'] == 'REJECTED_CONTACT_FIT':
            context_shots = [s for s in shots if s[0] == 'character']
        shots = [
            ('fretting-front', center + offset @ Vector((0, 0, .6)), center, .27),
            ('fretting-oblique', center + offset @ Vector((.12, .20, .4)), center, .27),
            ('fretting-rear', center + offset @ Vector((-.02, .14, -.4)), center, .27),
        ] + context_shots
    if args.mode == 'groom-build':
        shots = [
            ('groom-front', (0, -2, 1.72), (0, 0, 1.70), .38),
            ('groom-oblique', (.8, -1.6, 1.86), (0, 0, 1.70), .38),
            ('groom-side', (1.8, 0, 1.74), (0, 0, 1.70), .38),
        ]
    report['preview'] = {'samples': scene.cycles.samples, 'size': size, 'threads': 2,
                         'reduced_detail': True, 'completed_shots': []}
    camera.data.type = 'ORTHO'
    for label, position, target, scale in shots:
        hidden = []
        if label == 'fretting-rear':
            for obj in scene.objects:
                if obj.type in {'MESH', 'CURVE', 'CURVES'} and not obj.hide_render and not obj.name.startswith(('V206_', 'V545_')):
                    hidden.append(obj); obj.hide_render = True
        camera.location = position
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        scene.render.filepath = str(out / f'{label}-preview.png')
        bpy.ops.render.render(write_still=True)
        for obj in hidden:
            obj.hide_render = False
        report['preview']['completed_shots'].append(label)
        (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
    if args.mode in ('review', 'build-review'):
        head = rig.pose.bones['Head']
        keys = bpy.data.objects['V416_BODY_CLEAN_JOIN'].data.shape_keys.key_blocks
        original = {side: head['Blink.' + side] for side in ('L', 'R')}
        report['blink_checks'] = []
        camera.location = (0, -2, 1.655)
        camera.rotation_euler = (Vector((0, 0, 1.655)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = .145
        scene.render.resolution_x = 640; scene.render.resolution_y = 320
        scene.cycles.samples = 24
        try:
            for value in (0., .5, 1.):
                for side in ('L', 'R'):
                    head['Blink.' + side] = value
                rig.update_tag(); bpy.context.view_layer.update()
                actual = {side: keys['Blink.' + side].value for side in ('L', 'R')}
                if any(abs(v - value) > 1e-5 for v in actual.values()):
                    raise RuntimeError(f'Blink driver did not evaluate: {value}, {actual}')
                scene.render.filepath = str(out / f'eyes-blink-{value:g}.png')
                bpy.ops.render.render(write_still=True)
                report['blink_checks'].append({'requested': value, 'shape_values': actual})
                (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
        finally:
            for side, value in original.items():
                head['Blink.' + side] = value
            rig.update_tag(); bpy.context.view_layer.update()
print(json.dumps(report))
