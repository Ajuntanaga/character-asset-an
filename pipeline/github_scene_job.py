"""Read a release scene and emit bounded previews and a scene report."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('check', 'preview', 'review', 'build-review', 'hand-build', 'groom-build', 'blink-build', 'guitar-build', 'combined-build'), default='check')
parser.add_argument('--output', default='results')
parser.add_argument('--facial-hair', action='store_true')
parser.add_argument('--reuse-hand', action='store_true')
parser.add_argument('--wrist-extension', action='store_true')
parser.add_argument('--axial-trial', action='store_true')
parser.add_argument('--delit-face', action='store_true')
parser.add_argument('--device', choices=('CPU', 'CUDA'), default='CPU')
parser.add_argument('--review-scope', choices=('full', 'mouth', 'appearance', 'portrait', 'hands', 'wardrobe', 'hair-layers'), default='full')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
if args.axial_trial and args.mode != 'hand-build':
    parser.error('--axial-trial requires --mode hand-build')
if args.wrist_extension and args.mode != 'hand-build':
    parser.error('--wrist-extension requires --mode hand-build')
if args.facial_hair and args.mode != 'blink-build':
    parser.error('--facial-hair requires --mode blink-build')
if args.delit_face and args.mode != 'combined-build':
    parser.error('--delit-face requires --mode combined-build')
if args.review_scope != 'full' and args.mode != 'combined-build' and not (
        args.mode == 'hand-build' and args.review_scope == 'hands'):
    parser.error('--review-scope requires combined-build, or hand-build with hands')
cuff_variant = os.environ.get('CUFF_VARIANT', 'baseline') or 'baseline'
if cuff_variant not in ('baseline', 'distance-weighted', 'wrist-fitted'):
    parser.error('Unknown CUFF_VARIANT')
if cuff_variant != 'baseline' and args.mode != 'hand-build':
    parser.error('Cuff trial requires hand-build')
if cuff_variant == 'distance-weighted' and not args.wrist_extension:
    parser.error('Cuff trial requires hand-build with wrist-extension')
if args.reuse_hand and not (args.mode == 'hand-build' and cuff_variant == 'wrist-fitted' and args.axial_trial and not args.wrist_extension):
    parser.error('--reuse-hand requires the pinned axial wrist-fitted trial without wrist extension')
render_device = {'requested': args.device, 'selected': 'CPU'}
if args.device == 'CUDA':
    def gpu_trace(stage):
        if os.environ.get('CHARACTER_GPU_TRACE') == '1':
            print(json.dumps({'gpu_stage': stage}), flush=True)
    gpu_trace('DEVICE_SETUP_START')
    preferences = bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type = 'CUDA'
    gpu_trace("DEVICE_REFRESH_START")
    preferences.refresh_devices()
    gpu_trace("DEVICE_REFRESH_DONE")
    devices = [device for device in preferences.devices if device.type == 'CUDA']
    if not devices:
        raise RuntimeError('CUDA requested but no CUDA GPU is available')
    # One GPU is sufficient for these previews. Do not silently fall back
    # to CPU and spend the remote budget without acceleration.
    selected = devices[0]
    for device in preferences.devices:
        device.use = device == selected
    render_device['selected'] = selected.name
    gpu_trace('DEVICE_SELECTED_' + selected.name)
out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
if args.mode == 'build-review':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_v544_reference_revision import build
    build(out)
if args.mode == 'hand-build':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if cuff_variant == 'distance-weighted':
        from refine_v630_left_cuff_weights import build as build_cuff
        build_cuff(out)
    if args.reuse_hand:
        assert 'V545_NATIVE_HAND.L' in bpy.data.objects
        assert (out / 'hand-fit-report.json').is_file()
        # Older pinned checkpoints predate the joint export. Read the loaded
        # evaluated pose without rerunning or accepting the rejected fit.
        bpy.context.view_layer.update()
        hand_rig = bpy.data.objects['V545_NATIVE_RIG.L'].evaluated_get(
            bpy.context.evaluated_depsgraph_get())
        instrument_inverse = bpy.data.objects['V206_GUITAR_ROOT'].matrix_world.inverted()
        to_instrument = instrument_inverse @ hand_rig.matrix_world
        fit_path = out / 'hand-fit-report.json'
        reused_fit = json.loads(fit_path.read_text())
        reused_fit['joints_guitar_local_m'] = {
            digit: [list(to_instrument @ hand_rig.pose.bones[f'DEF-Finger_{digit}{j}.R'].head)
                    for j in (1, 2, 3)] +
                   [list(to_instrument @ hand_rig.pose.bones[f'DEF-Finger_{digit}3.R'].tail)]
            for digit in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')}
        reused_fit['wrist_guitar_local_m'] = list(
            to_instrument @ hand_rig.pose.bones['DEF-Hand.R'].head)
        reused_fit['joint_export_source'] = 'evaluated_reused_checkpoint'
        fit_path.write_text(json.dumps(reused_fit, indent=2))
    else:
        from build_v545_fretting_hand import build
        build(out, thumb_support='sliding_rear', relaxed_contact_dips=True, spread_trial=True, wrist_extension=args.wrist_extension, axial_trial=args.axial_trial, hover_orientation_trial=args.axial_trial, middle_axial_trial=args.axial_trial)
    if cuff_variant == 'wrist-fitted':
        from build_v742_wrist_fitted_cuff import build as build_cuff
        cuff, cuff_report = build_cuff()
        source_cuff = bpy.data.objects['V357_CUFF_PATCH.L']
        source_cuff.hide_render = True
        source_cuff.hide_set(True)
        (out / 'wrist-fitted-cuff-report.json').write_text(json.dumps(cuff_report, indent=2))
        bpy.ops.wm.save_as_mainfile(filepath=str((out / 'Character_An_fretting_hand_TRIAL_v545.blend').resolve()))
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
        if args.wrist_extension or cuff_variant == 'wrist-fitted':
            wrist = rig.matrix_world @ rig.pose.bones['DEF-Hand.L'].head
            shots += [(f'wrist-{angle}', wrist + offset @ Vector((0, 0, .6)), wrist, .23) for angle in (0, -15, 15)]
            if cuff_variant == 'wrist-fitted':
                shots += [(f'wrist-15-{layer}', wrist + offset @ Vector((0, 0, .6)), wrist, .23)
                          for layer in ('without-cuff', 'without-body')]
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
        # Resolve the bridge from the actual saddle positions, not a guessed
        # body coordinate. These crops distinguish geometry from preview detail.
        bridge = sum((bpy.data.objects[f'V206_SADDLE_S{i}'].matrix_world.translation
                      for i in range(1, 9)), Vector()) / 8
        axes = guitar.matrix_world.to_quaternion()
        bridge += axes @ Vector((.015, 0, .015))
        shots += [
            ('guitar-hardware-front', bridge + axes @ Vector((0, 0, .5)), bridge, .15),
            ('guitar-hardware-oblique', bridge + axes @ Vector((.20, -.18, .40)), bridge, .15),
        ]
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
        elif args.review_scope == 'portrait':
            shots = [shot for shot in shots if shot[0].startswith('face-')]
        elif args.review_scope == 'hair-layers':
            # Identical cameras and lighting distinguish scanned cap geometry
            # from the generated curl bundles; never save the isolated state.
            shots = [
                ('hair-full-front', (0, -2, 1.72), (0, 0, 1.70), .38),
                ('hair-underlay-front', (0, -2, 1.72), (0, 0, 1.70), .38),
                ('hair-full-oblique', (.8, -1.6, 1.86), (0, 0, 1.70), .38),
                ('hair-underlay-oblique', (.8, -1.6, 1.86), (0, 0, 1.70), .38),
            ]
        elif args.review_scope == 'wardrobe':
            shots = [
                ('wardrobe-stitch-before', (0,-2,1.29), (0,0,1.29), .4956),
                ('wardrobe-stitch-after', (0,-2,1.29), (0,0,1.29), .4956),
                ('wardrobe-stitch-oblique', (.6,-2,1.29), (0,0,1.29), .4956),
                ('character', (.35,-3.5,1.3), (0,0,.94), 2.12),
            ]
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
        if label.startswith('hair-'):
            scene.cycles.samples = 64
        if label.startswith('hair-underlay-'):
            for obj in scene.objects:
                if obj.name.endswith('_CURL_GROOM') and not obj.hide_render:
                    hidden.append(obj)
                    obj.hide_render = True
            if not hidden:
                raise RuntimeError('Hair isolation found no visible curl groom')
            report.setdefault('hair_layer_checks', []).append({
                'shot': label, 'hidden_grooms': [obj.name for obj in hidden],
                'retained_underlay': 'V371_DARK_HAIR_UNDERLAY',
            })
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
        if label == 'wardrobe-stitch-before':
            for name in ('V596_POCKET_TOPSTITCH_TRIAL', 'V600_POCKET_SNAP_COVERS'):
                detail=bpy.data.objects.get(name)
                if detail is not None and not detail.hide_render:
                    hidden.append(detail); detail.hide_render=True
        if label.startswith('wardrobe-'):
            for obj in bpy.data.objects['V206_GUITAR_ROOT'].children_recursive:
                if not obj.hide_render:
                    hidden.append(obj); obj.hide_render = True
        if label == 'fretting-rear':
            for obj in scene.objects:
                if obj.type in {'MESH', 'CURVE', 'CURVES'} and not obj.hide_render and not obj.name.startswith(('V206_', 'V545_')):
                    hidden.append(obj); obj.hide_render = True
        if label.startswith('guitar-'):
            guitar_parts = set(guitar.children_recursive)
            for obj in scene.objects:
                if obj.type in {'MESH', 'CURVE', 'CURVES'} and not obj.hide_render and obj not in guitar_parts:
                    hidden.append(obj); obj.hide_render = True
        wrist_control = None
        if label.startswith('wrist-'):
            # Isolate the cuff and wrist surface; the guitar obscures this view.
            # Normal grip views above retain the instrument for contact review.
            for obj in bpy.data.objects['V206_GUITAR_ROOT'].children_recursive:
                if not obj.hide_render:
                    hidden.append(obj); obj.hide_render = True
            wrist_control = rig.pose.bones['IK-Hand.L']
            saved_wrist = wrist_control.matrix_basis.copy()
            angle_label = label[len('wrist-'):]
            for suffix, object_name in (
                    ('-without-cuff', 'V742_WRIST_FITTED_CUFF.L'),
                    ('-without-body', 'V416_BODY_CLEAN_JOIN')):
                if angle_label.endswith(suffix):
                    angle_label = angle_label.removesuffix(suffix)
                    obj = bpy.data.objects[object_name]
                    if not obj.hide_render:
                        hidden.append(obj)
                        obj.hide_render = True
            angle = int(angle_label)
            wrist_control.matrix_basis = saved_wrist @ Matrix.Rotation(math.radians(angle), 4, 'X')
            rig.update_tag(); bpy.context.view_layer.update()
            scene.cycles.samples = 16
            scene.render.resolution_x = scene.render.resolution_y = 512
        camera.location = position
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        if label in {'guitar-front', 'guitar-hardware-front'}:
            camera.rotation_euler = (guitar.matrix_world.to_3x3() @ Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))).to_euler()
        camera.data.ortho_scale = scale
        scene.render.filepath = str(out / f'{label}-preview.png')
        bpy.ops.render.render(write_still=True)
        if wrist_control is not None:
            wrist_control.matrix_basis = saved_wrist
            rig.update_tag(); bpy.context.view_layer.update()
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
    if args.review_scope not in ('mouth', 'hands', 'wardrobe', 'hair-layers') and args.mode in ('review', 'build-review', 'blink-build', 'combined-build'):
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
