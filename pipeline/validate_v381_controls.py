"""Inspect asymmetric facial controls and the oral seam from an oblique view."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v381_facial_controls'
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
names = ('Smile.L','Smile.R','JawOpen','Blink.L','Blink.R',
         'BrowDown.L','BrowDown.R','BrowOuterUp.L','BrowOuterUp.R','BrowInnerUp')
saved = {name:head[name] for name in names}
assert len(rig.animation_data.drivers) == 1957
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 40
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = .37
try:
    poses = [
        ('v381_smile_jaw_threequarter.png',(.75,-1.4,1.66),
         {'Smile.L':.7,'Smile.R':.7,'JawOpen':.5,'BrowInnerUp':.25}),
        ('v381_asymmetric_brow_blink.png',(0,-1.4,1.66),
         {'BrowDown.L':.4,'BrowOuterUp.R':.5,'Blink.L':1.,'BrowInnerUp':.2}),
    ]
    for filename,location,values in poses:
        for name in names:
            head[name] = 0.
        for name,value in values.items():
            head[name] = value
        rig.update_tag()
        bpy.context.view_layer.update()
        scene.camera.location = location
        scene.camera.rotation_euler = (Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath = str(OUT/filename)
        bpy.ops.render.render(write_still=True)
finally:
    for name,value in saved.items():
        head[name] = value
    rig.update_tag()
    bpy.context.view_layer.update()
assert len(rig.animation_data.drivers) == 1957
print(json.dumps({'restored_controls':saved,'rig_drivers':1957}))
