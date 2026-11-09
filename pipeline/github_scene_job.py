"""Read a release scene and emit a bounded CPU preview and scene report."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('check', 'preview'), default='check')
parser.add_argument('--output', default='results')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
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
if args.mode == 'preview':
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.render.use_simplify = True
    scene.render.simplify_subdivision_render = 1
    scene.render.simplify_child_particles_render = 0.1
    scene.render.resolution_x = 512; scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    camera = scene.camera
    if camera is None:
        raise RuntimeError('Scene camera missing')
    camera.location = (-.00624775, -.645, .74370837)
    camera.rotation_euler = (Vector((-.10234958, -.27, 1.0314399)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'; camera.data.ortho_scale = .42
    scene.render.filepath = str(out / 'instrument-preview.png')
    bpy.ops.render.render(write_still=True)
    report['preview'] = {'samples': 8, 'size': 512, 'threads': 2, 'reduced_detail': True}
    (out / 'scene-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
