"""Bounded remote rig generation and GPU hand inspection; no local bpy process."""
import hashlib
import json
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
app = modal.App('character-asset-an-process-v352')
volume = modal.Volume.from_name('character-asset-an', create_if_missing=False)
image = (
    modal.Image.debian_slim(python_version='3.13')
    .apt_install('libx11-6', 'libxrender1', 'libxfixes3', 'libxi6',
                 'libxxf86vm1', 'libxkbcommon0', 'libgl1', 'libsm6', 'libice6')
    .pip_install('bpy==5.2.2')
    .add_local_dir(ROOT / 'third_party/cloudrig/source', '/opt/addons/cloudrig',
                   ignore=['**/__pycache__/**', '**/*.pyc'])
    .add_local_file(ROOT / 'pipeline/repair_v352_finger_axes.py', '/opt/repair.py')
)


@app.function(image=image, cpu=(4, 4), memory=(8192, 16384), timeout=900,
              max_containers=1, volumes={'/assets': volume})
def repair(remote_source: str, remote_output: str):
    import os
    import runpy
    import traceback
    out = Path('/assets' + remote_output)
    out.mkdir(parents=True, exist_ok=True)
    os.environ['BCA_SOURCE'] = '/assets' + remote_source
    os.environ['BCA_OUTPUT'] = str(out)
    try:
        runpy.run_path('/opt/repair.py', run_name='__main__')
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        volume.commit()
    return json.loads((out / 'finger_axis_report.json').read_text())


@app.function(image=image, gpu='L4', cpu=(2, 4), memory=(8192, 16384), timeout=1200,
              max_containers=1, volumes={'/assets': volume})
def render(remote_output: str):
    import bpy
    from mathutils import Vector
    volume.reload()
    out = Path('/assets' + remote_output)
    bpy.context.preferences.filepaths.use_scripts_auto_execute = True
    bpy.ops.wm.open_mainfile(filepath=str(out / 'Character_An_CloudRig_hands_pose_v352.blend'))
    scene = bpy.data.scenes['V352_CLOUDRIG_HANDS']
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.cycles.device = 'GPU'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    devices = []
    for device in prefs.devices:
        device.use = device.type != 'CPU'
        if device.use:
            devices.append(device.name)
    if not devices:
        raise RuntimeError('No GPU available for rendering')
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_percentage = 100
    scene.render.resolution_x, scene.render.resolution_y = 900, 1000
    camera = scene.camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .27
    images = []
    for frame, label in ((1, 'open'), (24, 'curl')):
        scene.frame_set(frame)
        for side, sign in (('L', 1), ('R', -1)):
            target = Vector((sign * .302, -.01, .82))
            camera.location = (sign * 1.2, -.18, .85)
            camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
            path = out / f'v352_hand_{side}_{label}.png'
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            images.append(path.name)
            volume.commit()
    (out / 'render_report.json').write_text(json.dumps({'devices': devices, 'images': images,
                                                       'samples': 48}, indent=2))
    volume.commit()
    return images


@app.local_entrypoint()
def main(reuse_source: bool = False):
    source = ROOT / 'production_v351_cloudrig_fingers/Character_An_CloudRig_hands_before_modal_v351.blend'
    dest = ROOT / 'production_v352_modal_finger_repair'
    dest.mkdir(exist_ok=True)
    with source.open('rb') as stream:
        source_hash = hashlib.file_digest(stream, 'sha256').hexdigest()[:16]
    code_hash = hashlib.sha256((ROOT / 'pipeline/repair_v352_finger_axes.py').read_bytes()).hexdigest()[:8]
    remote_source = '/input/' + source_hash + '.blend'
    remote_output = f'/processing/v352_{source_hash}_{code_hash}'
    manifest = {'input': str(source), 'remote_source': remote_source,
                'remote_output': remote_output, 'status': 'uploading'}
    manifest_path = dest / 'modal_run.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    if not reuse_source:
        with volume.batch_upload(force=True) as upload:
            upload.put_file(source, remote_source)
    manifest['status'] = 'remote_rig_running'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    try:
        report = repair.remote(remote_source, remote_output)
    except Exception as exc:
        manifest.update(status='remote_rig_failed', error=str(exc))
        manifest_path.write_text(json.dumps(manifest, indent=2))
        raise
    (dest / 'finger_axis_report.json').write_text(json.dumps(report, indent=2))
    manifest['status'] = 'remote_gpu_rendering'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    try:
        images = render.remote(remote_output)
    except Exception as exc:
        manifest.update(status='remote_render_failed', error=str(exc))
        manifest_path.write_text(json.dumps(manifest, indent=2))
        raise
    names = ['render_report.json', *images, 'Character_An_CloudRig_hands_v352.blend',
             'Character_An_CloudRig_hands_pose_v352.blend']
    manifest['status'] = 'downloading'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    for name in names:
        partial = dest / (name + '.part')
        with partial.open('wb') as output:
            for chunk in volume.read_file(remote_output + '/' + name):
                output.write(chunk)
        partial.replace(dest / name)
    manifest['status'] = 'downloaded_pending_visual_review'
    manifest['outputs'] = names
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
