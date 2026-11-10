"""Isolate scene loading and one-GPU rendering from character reconstruction."""
import json
from pathlib import Path
import resource
import bpy

out = Path('/kaggle/working/results')
report = {'purpose': 'GPU diagnostic only; not character quality validation'}


def stage(name):
    report['stage'] = name
    report['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(report), flush=True)
    (out / 'gpu-smoke-report.json').write_text(json.dumps(report, indent=2))


rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
report['main_drivers'] = len(rig.animation_data.drivers)
assert report['main_drivers'] == 1957
stage('SCENE_LOADED')
preferences = bpy.context.preferences.addons['cycles'].preferences
preferences.compute_device_type = 'CUDA'
stage('CUDA_ENUMERATION_START')
preferences.refresh_devices()
gpus = [device for device in preferences.devices if device.type == 'CUDA']
assert gpus, 'No CUDA GPU found'
for device in preferences.devices:
    device.use = device == gpus[0]
report['gpu'] = gpus[0].name
stage('CUDA_READY')
# A new empty scene avoids evaluating or rendering the character during this probe.
scene = bpy.data.scenes.new('GPU_SMOKE_ONLY')
bpy.context.window.scene = scene
camera_data = bpy.data.cameras.new('GPU_SMOKE_CAMERA')
camera = bpy.data.objects.new('GPU_SMOKE_CAMERA', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
scene.world = bpy.data.worlds.new('GPU_SMOKE_WORLD')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18, .18, .18, 1)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 1
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.resolution_x = scene.render.resolution_y = 32
scene.render.resolution_percentage = 100
scene.render.filepath = str(out / 'gpu-smoke.png')
stage('RENDER_START')
bpy.ops.render.render(write_still=True)
assert (out / 'gpu-smoke.png').stat().st_size > 0
stage('GPU_SMOKE_PASSED')
