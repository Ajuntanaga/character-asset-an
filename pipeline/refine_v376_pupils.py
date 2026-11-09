"""Correct the free eye asset's inverted pupil control; render in the live GUI."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v376_face_refinement'
OUT.mkdir(exist_ok=True)
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
for side in ('L', 'R'):
    eye = bpy.data.objects['V374_EYE.' + side]
    # The authored endpoint called Dilation contracts the aperture.
    eye.data.shape_keys.key_blocks['Dilation'].value = .75
material = bpy.data.objects['V374_EYE.L'].data.materials[0]
group = next(n for n in material.node_tree.nodes if n.type == 'GROUP')
for name, color in {
    'Iris Primary': (.080, .030, .0075, 1),
    'Iris Secondary': (.20, .088, .024, 1),
    'Iris Tertiary': (.115, .046, .014, 1),
    'Splotches': (.22, .090, .023, 1),
}.items():
    group.inputs[name].default_value = color
bpy.context.view_layer.update()
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x, scene.render.resolution_y = 800, 450
scene.camera.data.ortho_scale = .17
scene.camera.location = (0, -1.4, 1.65)
scene.camera.rotation_euler = (Vector((0, 0, 1.65))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = str(OUT/'v376_pupil_check.png')
bpy.ops.render.render(write_still=True)

# Load only a hidden projection donor. Its geometry is never made visible.
donor = bpy.data.objects.get('V376_FACE_PHOTO_DONOR')
if donor is None:
    with bpy.data.libraries.load(str(ROOT/'production_v326_photoreal_facebuilder/Character_An_photoreal_head_v326.blend'), link=False) as (_, loaded):
        loaded.objects = ['V326_PHOTOREAL_FACEBUILDER_HEAD']
    donor = loaded.objects[0]
    donor.name = 'V376_FACE_PHOTO_DONOR'
    donor.hide_render = donor.hide_viewport = True
mesh = donor.data
mesh.calc_loop_triangles()
data = {
    'vertices': [list(donor.matrix_world @ v.co) for v in mesh.vertices],
    'triangles': [list(t.vertices) for t in mesh.loop_triangles],
    'triangle_uvs': [[list(mesh.uv_layers.active.data[i].uv) for i in t.loops] for t in mesh.loop_triangles],
    'shape_keys': list(mesh.shape_keys.key_blocks.keys()),
    'matrix': [list(row) for row in donor.matrix_world],
}
(OUT/'photo_donor_geometry.json').write_text(json.dumps(data))
print(json.dumps({'pupil_contraction': .75, 'rig_drivers': len(rig.animation_data.drivers),
                  'donor_vertices': len(mesh.vertices), 'donor_visible': False}))
