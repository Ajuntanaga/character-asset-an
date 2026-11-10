"""Read a release scene and emit bounded previews and a scene report."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('check', 'preview', 'review', 'build-review', 'hand-build', 'groom-build', 'blink-build', 'guitar-build', 'combined-build'), default='check')
parser.add_argument('--output', default='results')
parser.add_argument('--facial-hair', action='store_true')
parser.add_argument('--delit-face', action='store_true')
parser.add_argument('--device', choices=('CPU', 'CUDA'), default='CPU')
parser.add_argument('--review-scope', choices=('full', 'mouth', 'appearance', 'hands'), default='full')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
if args.facial_hair and args.mode != 'blink-build':
    parser.error('--facial-hair requires --mode blink-build')
if args.delit_face and args.mode != 'combined-build':
    parser.error('--delit-face requires --mode combined-build')
if args.review_scope != 'full' and args.mode != 'combined-build':
    parser.error('--review-scope mouth/appearance/hands requires --mode combined-build')
render_device = {'requested': args.device, 'selected': 'CPU'}
if args.device == 'CUDA':
    preferences = bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type = 'CUDA'
    preferences.refresh_devices()
    devices = [device for device in preferences.devices if device.type == 'CUDA']
    if not devices:
        raise RuntimeError('CUDA requested but no CUDA GPU is available')
    # One GPU is sufficient for these previews. Do not silently fall back
    # to CPU and spend the remote budget without acceleration.
    selected = devices[0]
    for device in preferences.devices:
        device.use = device == selected
    render_device['selected'] = selected.name
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
if args.mode == 'blink-build':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_v547_blink_alignment import build
    build(Path(__file__).resolve().parents[1], out)
    if args.facial_hair:
        from refine_v551_beard_length import build as build_beard
        build_beard(out)
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve() / 'Character_An_blink_alignment_TRIAL_v547.blend'), compress=True)
if args.mode == 'guitar-build':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from refine_v550_maple_density import build
    build(out)
if args.mode == 'combined-build':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_v554_combined_trial import build
    build(out, delit_face=args.delit_face)
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
          'mode': args.mode, 'review_scope': args.review_scope,
          'quality_status': 'WORK_IN_PROGRESS_NOT_ACCEPTED'}
(out / 'scene-report.json').write_text(json.dumps(report, indent=2))
if args.mode in ('preview', 'review', 'build-review', 'hand-build', 'groom-build', 'blink-build', 'guitar-build', 'combined-build'):
    review = args.mode != 'preview'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU' if args.device == 'CUDA' else 'CPU'
    report['render_device'] = render_device
    (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
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
        if fit['status'].startswith('REJECTED'):
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
    if args.mode == 'blink-build':
        shots = [
            ('face-front', (0, -2, 1.68), (0, 0, 1.65), .40),
            ('face-clay', (.30, -2, 1.70), (0, 0, 1.65), .40),
            ('wardrobe-front', (0, -3, 1.24), (0, 0, 1.24), .94),
        ]
        if args.facial_hair:
            shots.append(('beard-detail', (.12, -.8, 1.58), (0, -.045, 1.557), .15))
    if args.mode == 'guitar-build':
        guitar = bpy.data.objects['V206_GUITAR_ROOT']
        shots = [('guitar-front', guitar.matrix_world @ Vector((.625, 0, 1.)),
                  guitar.matrix_world @ Vector((.625, 0, 0)), .55), shots[0]]
    if args.mode == 'combined-build':
        guitar = bpy.data.objects['V206_GUITAR_ROOT']
        shots = [
            ('face-front', (0, -2, 1.68), (0, 0, 1.65), .40),
            ('face-profile', (2, 0, 1.65), (0, 0, 1.65), .40),
            ('face-oblique', (.70, -1.7, 1.78), (0, 0, 1.67), .40),
            ('wardrobe-collar-front', (0, -2, 1.48), (0, 0, 1.43), .48),
            ('wardrobe-collar-oblique', (.60, -1.6, 1.56), (0, 0, 1.44), .48),
            ('wardrobe-collar-rear', (0, 2, 1.60), (0, .06, 1.52), .28),
            ('character', (.35, -3.5, 1.3), (0, 0, .94), 2.12),
        ]
        if args.delit_face:
            shots = [shots[0],
                     ('face-profile', (2, 0, 1.65), (0, 0, 1.65), .40),
                     ('face-oblique', (.70, -1.7, 1.68), (0, 0, 1.65), .40),
                     ('face-clay', (.30, -2, 1.70), (0, 0, 1.65), .40)]
        if args.review_scope == 'mouth':
            shots = [shot for shot in shots if shot[0] in ('face-front', 'face-oblique')]
        elif args.review_scope == 'hands':
            shots = [
                ('pick-grip', center + Vector((.13, -.20, .04)), center, .20),
                ('pick-dorsal', center + Vector((-.10, -.24, .12)), center, .20),
                ('character', (.35, -3.5, 1.3), (0, 0, .94), 2.12),
            ]
    report['preview'] = {'samples': scene.cycles.samples, 'size': size, 'threads': 2,
                         'reduced_detail': True, 'completed_shots': []}
    camera.data.type = 'ORTHO'
    for label, position, target, scale in shots:
        hidden = []
        override = bpy.context.view_layer.material_override
        shape_key = None
        photo_gain = None
        if args.mode == 'combined-build' and label.startswith('face-'):
            scene.cycles.samples = 64
        if label == 'face-source-before':
            photo_gain = bpy.data.materials['V563_DIRECT_FRONT_PHOTO_SKIN'].node_tree.nodes['V563_FrontPhotoGain'].inputs[1]
            saved_photo_gain = photo_gain.default_value
            photo_gain.default_value = 0.
            bpy.context.view_layer.update()
        if label.startswith('face-clay-'):
            shape_key = bpy.data.objects['V416_BODY_CLEAN_JOIN'].data.shape_keys.key_blocks['V560_ReferenceCentralFace']
            saved_shape_value = shape_key.value
            if label.endswith('-before'):
                shape_key.value = 0.
            bpy.context.view_layer.update()
        if label.startswith('face-clay'):
            clay = bpy.data.materials.new('DIAGNOSTIC_NEUTRAL_CLAY')
            clay.use_nodes = True
            bsdf = clay.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = (.32, .32, .32, 1)
            bsdf.inputs['Roughness'].default_value = .75
            bpy.context.view_layer.material_override = clay
            scene.cycles.samples = 16
            scene.render.resolution_x = scene.render.resolution_y = 512
        if label.startswith('wardrobe-'):
            for obj in bpy.data.objects['V206_GUITAR_ROOT'].children_recursive:
                if not obj.hide_render:
                    hidden.append(obj); obj.hide_render = True
        if label == 'fretting-rear':
            for obj in scene.objects:
                if obj.type in {'MESH', 'CURVE', 'CURVES'} and not obj.hide_render and not obj.name.startswith(('V206_', 'V545_')):
                    hidden.append(obj); obj.hide_render = True
        if label == 'guitar-front':
            guitar_parts = set(guitar.children_recursive)
            for obj in scene.objects:
                if obj.type in {'MESH', 'CURVE', 'CURVES'} and not obj.hide_render and obj not in guitar_parts:
                    hidden.append(obj); obj.hide_render = True
        camera.location = position
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        if label == 'guitar-front':
            camera.rotation_euler = (guitar.matrix_world.to_3x3() @ Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))).to_euler()
        camera.data.ortho_scale = scale
        scene.render.filepath = str(out / f'{label}-preview.png')
        bpy.ops.render.render(write_still=True)
        if photo_gain is not None:
            photo_gain.default_value = saved_photo_gain
            bpy.context.view_layer.update()
        if shape_key is not None:
            shape_key.value = saved_shape_value
            bpy.context.view_layer.update()
        bpy.context.view_layer.material_override = override
        scene.cycles.samples = report['preview']['samples']
        scene.render.resolution_x = scene.render.resolution_y = size
        for obj in hidden:
            obj.hide_render = False
        report['preview']['completed_shots'].append(label)
        (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
    if args.review_scope not in ('mouth', 'hands') and args.mode in ('review', 'build-review', 'blink-build', 'combined-build'):
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
            # Inspect the corneal clearance and closure from a different angle.
            camera.location = (.8, -1.6, 1.66)
            camera.rotation_euler = (Vector((0, 0, 1.655)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            for value in (.5, 1.):
                for side in ('L', 'R'):
                    head['Blink.' + side] = value
                rig.update_tag(); bpy.context.view_layer.update()
                scene.render.filepath = str(out / f'eyes-oblique-blink-{value:g}.png')
                bpy.ops.render.render(write_still=True)
                report['blink_checks'].append({'requested': value, 'view': 'oblique'})
                (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
        finally:
            for side, value in original.items():
                head['Blink.' + side] = value
            rig.update_tag(); bpy.context.view_layer.update()
    if args.mode == 'combined-build' and args.review_scope in ('full', 'mouth'):
        head = rig.pose.bones['Head']
        original = {name: head[name] for name in ('MouthPucker', 'JawOpen')}
        report['mouth_checks'] = []
        camera.data.ortho_scale = .15
        scene.render.resolution_x = scene.render.resolution_y = 640
        scene.cycles.samples = 48
        try:
            for label, pucker, jaw, position in (
                    ('mouth-neutral', 0., 0., (0, -2, 1.565)),
                    ('mouth-pucker', .45, 0., (0, -2, 1.565)),
                    ('mouth-pucker-jaw-oblique', .45, .45, (.3, -1.6, 1.60))):
                head['MouthPucker'], head['JawOpen'] = pucker, jaw
                rig.update_tag(); bpy.context.view_layer.update()
                actual = {name: bpy.data.objects[name].data.shape_keys.key_blocks['MouthPucker'].value
                          for name in ('V416_BODY_CLEAN_JOIN', 'V363_LIPS',
                                       'V363_MOUTH_CAVITY', 'V395_BEARD_FIBERS')}
                assert all(abs(v - pucker) < 1e-6 for v in actual.values()), actual
                camera.location = position
                camera.rotation_euler = (Vector((0, 0, 1.565)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
                scene.render.filepath = str(out / f'{label}-preview.png')
                bpy.ops.render.render(write_still=True)
                report['mouth_checks'].append({'view': label, 'pucker': pucker,
                                               'jaw': jaw, 'shape_values': actual})
                (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
        finally:
            for name, value in original.items():
                head[name] = value
            rig.update_tag(); bpy.context.view_layer.update()
print(json.dumps(report))
