"""Save the compact groom and collect landmarks for a photo-texture donor."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v376_face_refinement'
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
donor = bpy.data.objects['V376_FACE_PHOTO_DONOR']
donor.use_fake_user = True
assert len(rig.animation_data.drivers) == 1957
keys = donor.data.shape_keys.key_blocks
basis = keys[0]
landmarks = {}
for key in keys:
    if key == basis:
        continue
    moved = [(i, (v.co-basis.data[i].co).length) for i,v in enumerate(key.data)]
    peak = max(d for _,d in moved)
    selected = [(i,d) for i,d in moved if d > peak*.35]
    weight = sum(d for _,d in selected)
    center = sum((basis.data[i].co*d for i,d in selected),Vector())/weight if weight else Vector()
    landmarks[key.name] = {'peak':peak,'centroid':list(center),'vertices':[i for i,_ in selected]}
(OUT/'photo_donor_shape_regions.json').write_text(json.dumps(landmarks))
head = [{'id':v.index,'co':list(body.matrix_world@v.co)} for v in body.data.vertices if (body.matrix_world@v.co).z>1.45]
(OUT/'current_head_geometry.json').write_text(json.dumps({'vertices':head,'matrix':[list(r) for r in body.matrix_world]}))
scene['V376_STATUS'] = 'COMPACT_CURLS_AND_PUPILS_SAVED_FACE_REFINEMENT_PENDING'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_compact_curls_v376.blend'),compress=True)
scene.render.resolution_x = scene.render.resolution_y = 800
scene.cycles.samples = 48
scene.render.threads_mode, scene.render.threads = 'FIXED',4
scene.camera.data.ortho_scale = .37
scene.camera.location = (.80,-1.25,1.69)
scene.camera.rotation_euler = (Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v376_compact_curls_threequarter.png')
bpy.ops.render.render(write_still=True)
print(json.dumps({'saved':bpy.data.filepath,'drivers':len(rig.animation_data.drivers),'donor_preserved':donor.use_fake_user}))
