"""Start one review render as a GUI job, leaving the MCP bridge responsive."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
request = json.loads((ROOT/'pipeline/render_preview_request.json').read_text())
assert not bpy.app.is_job_running('RENDER'), 'Wait for the current render first'
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
head = rig.pose.bones['Head']
for name, value in request.get('controls', {}).items():
    assert name in head
    head[name] = float(value)
rig.update_tag()
bpy.context.view_layer.update()
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = request.get('samples', 32)
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 4
scene.render.use_persistent_data = False
scene.render.resolution_x, scene.render.resolution_y = request['resolution']
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = request['scale']
scene.camera.location = request['camera']
scene.camera.rotation_euler = (Vector(request['target'])-scene.camera.location).to_track_quat('-Z','Y').to_euler()
destination = ROOT/request['output']
destination.parent.mkdir(exist_ok=True)
scene.render.filepath = str(destination)
result = bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
print(json.dumps({'render_operator':list(result), 'output':str(destination),
                  'rig_drivers':len(rig.animation_data.drivers)}))
