"""Reduce the guitar's regular zebra contrast, preserving its reference outline."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v380_guitar_finish'
OUT.mkdir(exist_ok=True)
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
material = bpy.data.materials['V356_GRAYBURST_FLAMED_MAPLE']
assert not material.get('V380_finish_applied')
assert len(rig.animation_data.drivers) == 1957
nodes, links = material.node_tree.nodes, material.node_tree.links
wave = next(n for n in nodes if n.type == 'TEX_WAVE')
ramp = next(n for n in nodes if n.type == 'VALTORGB')
shader = nodes['Principled BSDF']
backup = {
    'wave':{k:wave.inputs[k].default_value for k in ('Scale','Distortion','Detail','Detail Scale')},
    'ramp':[(e.position,list(e.color)) for e in ramp.color_ramp.elements],
    'roughness':shader.inputs['Roughness'].default_value,
    'coat':shader.inputs['Coat Weight'].default_value,
}
(OUT/'before_v380.json').write_text(json.dumps(backup,indent=2))
# The photo has roughly forty soft ripples along the body. Keep a continuous
# gradient: clipping the ramp would recreate hard zebra bands at any scale.
wave.inputs['Scale'].default_value = 19.
wave.inputs['Distortion'].default_value = 2.1
wave.inputs['Detail'].default_value = 4.
wave.inputs['Detail Scale'].default_value = 1.8
ramp.color_ramp.interpolation = 'EASE'
ramp.color_ramp.elements[0].position = 0.
ramp.color_ramp.elements[0].color = (.090,.107,.098,1.)
ramp.color_ramp.elements[1].position = 1.
ramp.color_ramp.elements[1].color = (.175,.201,.184,1.)
shader.inputs['Roughness'].default_value = .32
shader.inputs['Coat Weight'].default_value = .10
# Broaden the dark perimeter without changing the silhouette or UV mapping.
burst = next(n for n in nodes if n.type == 'TEX_IMAGE')
mix = next(n for n in nodes if n.type == 'MIX_RGB')
power = nodes.new('ShaderNodeMath')
power.name = 'V380_BurstFalloff'
power.operation = 'POWER'
power.inputs[1].default_value = 1.8
links.new(burst.outputs['Color'],power.inputs[0])
links.new(power.outputs[0],mix.inputs[0])
material['V380_finish_applied'] = True
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.render.resolution_x,scene.render.resolution_y = 1000,800
scene.render.resolution_percentage = 100
scene.camera.data.ortho_scale = 1.0
scene.camera.location = (0,-2.4,1.08)
scene.camera.rotation_euler = (Vector((0,0,1.08))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v380_guitar_finish.png')
bpy.ops.render.render(write_still=True)
report = {'material':material.name,'geometry_changed':False,
          'wave_scale':19.,'rig_drivers':len(rig.animation_data.drivers)}
(OUT/'guitar_finish_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
