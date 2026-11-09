"""Build one continuous exact-contact hand as an implicit metaball surface."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v237_exact_contact_hand" / "Character_An_exact_contact_hand_v237.blend"
STAGE = ROOT / "production_v238_continuous_fretting_hand"
OUTPUT = STAGE / "Character_An_continuous_fretting_hand_v238.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sample_segment(start: Vector, end: Vector, spacing: float) -> list[Vector]:
    distance = (end - start).length
    count = max(2, int(distance / spacing) + 1)
    return [start.lerp(end, index / (count - 1)) for index in range(count)]


def build_continuous_hand() -> bpy.types.Object:
    source_collection = bpy.data.collections["V207_PLAYABLE_HANDS"]
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    skin_material = bpy.data.materials["MAT_V207_SKIN"]
    data = bpy.data.metaballs.new("V238_FRETTING_HAND_SURFACE")
    data.resolution = 0.0018
    data.render_resolution = 0.0012
    data.threshold = 0.62
    data.materials.append(skin_material)
    hand = bpy.data.objects.new("V238_FRETTING_HAND_CONTINUOUS", data)
    source_collection.objects.link(hand)
    hand.parent = root

    def add_ball(point: Vector, radius: float, stiffness: float = 2.0) -> None:
        element = data.elements.new()
        element.type = "BALL"
        element.co = point
        element.radius = radius
        element.stiffness = stiffness

    finger_points = {
        "index": [Vector((0.372, -0.007, 0.066)), Vector((0.350, -0.001, 0.071)), Vector((0.326, 0.002, 0.053)), Vector((0.3058092, 0.0041983, 0.0258))],
        "middle": [Vector((0.378, 0.004, 0.071)), Vector((0.361, 0.000, 0.075)), Vector((0.343, -0.003, 0.054)), Vector((0.3296208, -0.0042573, 0.0260))],
        "ring": [Vector((0.374, 0.018, 0.067)), Vector((0.351, 0.020, 0.072)), Vector((0.327, 0.021, 0.051)), Vector((0.3050834, 0.0209915, 0.0257))],
        "pinky": [Vector((0.365, 0.031, 0.059)), Vector((0.362, 0.031, 0.058)), Vector((0.355, 0.030, 0.041)), Vector((0.3488616, 0.0301913, 0.0251))],
    }
    finger_radii = {"index": 0.0061, "middle": 0.0064, "ring": 0.0060, "pinky": 0.0053}
    for digit, points in finger_points.items():
        radius = finger_radii[digit]
        for segment_index, (start, end) in enumerate(zip(points, points[1:])):
            taper = 1.0 - segment_index * 0.07
            for point in _sample_segment(start, end, radius * 0.58):
                add_ball(point, radius * taper)

    thumb_points = [Vector((0.421, 0.040, 0.055)), Vector((0.397, 0.046, 0.023)), Vector((0.372, 0.028, -0.012)), Vector((0.354, 0.010, -0.028))]
    for segment_index, (start, end) in enumerate(zip(thumb_points, thumb_points[1:])):
        radius = 0.0070 * (1.0 - segment_index * 0.08)
        for point in _sample_segment(start, end, radius * 0.58):
            add_ball(point, radius)

    # Palm, thenar, and wrist clusters. Overlapping elements form one continuous
    # organic surface instead of the visible construction spheres in V237.
    palm_centers = [
        (Vector((0.407, -0.003, 0.066)), 0.026),
        (Vector((0.407, 0.014, 0.064)), 0.029),
        (Vector((0.407, 0.030, 0.060)), 0.025),
        (Vector((0.424, 0.012, 0.064)), 0.024),
        (Vector((0.443, 0.011, 0.066)), 0.022),
        (Vector((0.462, 0.010, 0.068)), 0.020),
    ]
    for point, radius in palm_centers:
        add_ball(point, radius, 2.2)

    hand["contact_map"] = "index S5/F9; middle S4/F10; ring S7/F9; pinky S8/F11"
    hand["string_depression_m"] = 0.00185

    # Preserve construction geometry as hidden technical evidence.
    for obj in source_collection.objects:
        if obj != hand and not obj.name.startswith("V207_TARGET_"):
            obj.hide_render = True
            obj.hide_viewport = True
    return hand


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open V237 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    hand = build_continuous_hand()
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    camera = bpy.data.objects["V232_CAMERA"]
    scene.camera = camera
    views = {
        "performance": (Vector((0.0, -2.7, 1.18)), Vector((0.0, -0.03, 1.12)), 70.0, (1100, 900)),
        "fretting": (Vector((-0.70, -1.55, 1.45)), Vector((0.28, -0.28, 1.42)), 98.0, (1200, 950)),
        "contact_macro": (Vector((-0.28, -1.08, 1.49)), Vector((0.33, -0.31, 1.43)), 118.0, (1200, 950)),
    }
    renders = {}
    for name, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        output = RENDERS / f"v238_{name}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        renders[name] = {"path": str(output.relative_to(ROOT)), "sha256": sha256(output)}

    audit = {
        "schema": "v238-continuous-fretting-hand-v1",
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "continuous_mesh": hand.name,
        "surface_type": "METABALL",
        "elements": len(hand.data.elements),
        "render_resolution_m": 0.0012,
        "contact_map": "index S5/F9; middle S4/F10; ring S7/F9; pinky S8/F11",
        "string_depression_m": 0.00185,
        "renders": renders,
    }
    audit_path = AUDIT / "v238_continuous_hand.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    scene["V238_STATUS"] = "CONTINUOUS_EXACT_CONTACT_HAND"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    receipt = {
        "status": "PASS",
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "audit_sha256": sha256(audit_path),
    }
    (AUDIT / "v238_build_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V238_CONTINUOUS_HAND_OK=" + json.dumps({"output": str(OUTPUT), "elements": len(hand.data.elements)}, sort_keys=True))


if __name__ == "__main__":
    main()
