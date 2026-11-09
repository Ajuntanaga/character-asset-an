"""Rigid-similarity fit V206 guitar landmarks to the proven V198 hand-aligned guitar."""

from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v232_v198_hybrid_world_head" / "Character_An_v198_hybrid_v232.blend"
SOURCE = ROOT / "production_v206_guitar" / "ant_headless_guitar_v206.blend"
OUT = ROOT / "production_v236_guitar_body_anchor_fit"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_guitar_body_anchor_v236.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))


def bounds_center(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return sum(corners, Vector()) / len(corners)


old_pairs = [
    ("ANTV1_GUITAR_BODY_EDGE", "V206_BODY_CORE"),
    ("ANTV1_GUITAR_NECK", "V206_NECK"),
    ("ANTV1_PICKUP_BRIDGE", "V206_PICKUP_BRIDGE"),
    ("ANTV1_PICKUP_NECK", "V206_PICKUP_NECK"),
]
targets = np.array([bounds_center(bpy.data.objects[old])[:] for old, _new in old_pairs], dtype=np.float64)

with bpy.data.libraries.load(str(SOURCE), link=False) as (data_from, data_to):
    data_to.collections = ["V206_GUITAR_REBUILD"]
collection = data_to.collections[0]
bpy.context.scene.collection.children.link(collection)
bpy.context.view_layer.update()
new_root = bpy.data.objects["V206_GUITAR_ROOT"]
root_inverse = new_root.matrix_world.inverted()
sources = np.array([(root_inverse @ bounds_center(bpy.data.objects[new]))[:] for _old, new in old_pairs], dtype=np.float64)
print({"targets": targets.tolist(), "sources": sources.tolist()})

# Umeyama similarity fit: sources in V206 root-local space to V198 world landmarks.
source_mean = sources.mean(axis=0)
target_mean = targets.mean(axis=0)
source_centered = sources - source_mean
target_centered = targets - target_mean
covariance = target_centered.T @ source_centered / len(sources)
u, singular, vt = np.linalg.svd(covariance)
sign = np.ones(3)
if np.linalg.det(u) * np.linalg.det(vt) < 0.0:
    sign[-1] = -1.0
rotation = u @ np.diag(sign) @ vt
variance = np.sum(source_centered ** 2) / len(sources)
similarity_scale = float(np.sum(singular * sign) / variance)
# The old and new pickup layouts are not metrically equivalent. Use them only to
# solve orientation, then anchor the body at a character-scale fit.
scale = 0.92
translation = targets[0] - scale * rotation @ sources[0]

transform = Matrix.Identity(4)
for row in range(3):
    for column in range(3):
        transform[row][column] = float(scale * rotation[row, column])
    transform[row][3] = float(translation[row])
new_root.matrix_world = transform
bpy.context.view_layer.update()

old_root = bpy.data.objects["ANTV1_GUITAR_ROOT"]
old_root.hide_render = True
old_root.hide_viewport = True
for obj in old_root.children_recursive:
    obj.hide_render = True
    obj.hide_viewport = True

fitted = np.array([bounds_center(bpy.data.objects[new])[:] for _old, new in old_pairs])
rms = float(np.sqrt(np.mean(np.sum((fitted - targets) ** 2, axis=1))))

camera = bpy.data.objects["V232_CAMERA"]


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.frame_set(1)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
views = {
    "full_front": (Vector((0.0, -4.4, 1.02)), Vector((0.0, 0.0, 0.98)), 58.0, (900, 1100)),
    "performance": (Vector((0.0, -2.7, 1.18)), Vector((0.0, -0.03, 1.12)), 70.0, (1100, 900)),
    "fretting": (Vector((-0.85, -1.8, 1.36)), Vector((0.20, -0.30, 1.40)), 88.0, (1000, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v236_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V236_STATUS"] = "V206_GUITAR_ORIENTATION_SOLVED_BODY_CENTER_ANCHORED"
scene["V236_LANDMARK_RMS_M"] = rms
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "orientation_similarity_scale": similarity_scale, "applied_scale": scale, "rms_m": rms})
