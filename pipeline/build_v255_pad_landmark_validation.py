"""Validate weight-derived fingertip pad landmarks visually on accepted V250."""

from pathlib import Path
import hashlib
import json
import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
STAGE = ROOT / "production_v255_pad_landmark_validation"
OUTPUT = STAGE / "Character_An_pad_landmarks_v255.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HAND = "V248_FRETTING_HAND_REALISTIC"
LANDMARKS = {"index": 234, "middle": 211, "ring": 14, "pinky": 225, "thumb": 286}
COLORS = {
    "index": (0.9, 0.08, 0.03, 1), "middle": (0.1, 0.75, 0.08, 1),
    "ring": (0.05, 0.25, 0.95, 1), "pinky": (0.9, 0.08, 0.75, 1),
    "thumb": (0.95, 0.65, 0.03, 1),
}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_vertex(hand, index):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    try:
        return evaluated.matrix_world @ mesh.vertices[index].co
    finally:
        evaluated.to_mesh_clear()


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V250 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True); RENDERS.mkdir(parents=True, exist_ok=True); AUDIT.mkdir(parents=True, exist_ok=True)
    hand = bpy.data.objects[HAND]
    record = {"schema": "v255-pad-landmark-validation-v1", "source": str(SOURCE.relative_to(ROOT)), "landmarks": {}}
    for digit, vertex in LANDMARKS.items():
        location = evaluated_vertex(hand, vertex)
        material = bpy.data.materials.new(f"V255_{digit.upper()}_PAD_MAT")
        material.diffuse_color = COLORS[digit]
        material.use_nodes = True
        material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = COLORS[digit]
        material.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = COLORS[digit]
        material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.0042, location=location)
        marker = bpy.context.object
        marker.name = f"V255_PAD_{digit.upper()}_V{vertex}"
        marker.data.materials.append(material)
        record["landmarks"][digit] = {"vertex": vertex, "world_m": [round(float(v), 7) for v in location]}

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    views = {
        "front": (Vector((0.72, -1.48, 1.49)), Vector((0.31, -0.45, 1.42)), 110.0),
        "oblique": (Vector((0.78, -0.83, 1.30)), Vector((0.31, -0.45, 1.42)), 105.0),
        "player_side": (Vector((0.56, 0.02, 1.42)), Vector((0.31, -0.43, 1.42)), 105.0),
    }
    record["renders"] = {}
    for label, (location, target, lens) in views.items():
        camera.location = location; camera.data.lens = lens; point_at(camera, target); scene.camera = camera
        scene.render.resolution_x = 1200; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
        path = RENDERS / f"v255_landmarks_{label}.png"
        scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
        record["renders"][label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    scene["V255_STATUS"] = "WEIGHT_DERIVED_PAD_LANDMARKS_VALIDATION"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)}
    (AUDIT / "v255_pad_landmarks.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V255_PAD_LANDMARKS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
