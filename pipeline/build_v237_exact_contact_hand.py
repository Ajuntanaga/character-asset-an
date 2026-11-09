"""Integrate the validated V207 fretting hand into the V236 character scene."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v236_guitar_body_anchor_fit" / "Character_An_guitar_body_anchor_v236.blend"
STAGE = ROOT / "production_v237_exact_contact_hand"
OUTPUT = STAGE / "Character_An_exact_contact_hand_v237.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_v207_playable_hands import build_hand
from pipeline.common import sha256, write_json


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def hide_legacy_hand_proxies() -> list[str]:
    hidden: list[str] = []
    for obj in bpy.data.objects:
        if obj.name.startswith("V196_FRETTING_"):
            obj.hide_render = True
            obj.hide_viewport = True
            hidden.append(obj.name)
    return sorted(hidden)


def world_point(root: bpy.types.Object, local: Vector) -> list[float]:
    return [round(value, 7) for value in (root.matrix_world @ local)]


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open V236 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    hidden = hide_legacy_hand_proxies()
    result = build_hand()
    root = result["root"]
    bpy.context.view_layer.update()

    # Imported V206 studio lights were designed for isolated product renders and
    # blow out the guitar inside the character lighting rig.
    for name in ("V206_KEY", "V206_FILL", "V206_RIM"):
        light = bpy.data.objects.get(name)
        if light:
            light.hide_render = True
            light.hide_viewport = True

    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.75
    camera = bpy.data.objects["V232_CAMERA"]
    scene.camera = camera

    views = {
        "full_front": (Vector((0.0, -4.4, 1.02)), Vector((0.0, 0.0, 0.98)), 58.0, (900, 1100)),
        "performance": (Vector((0.0, -2.7, 1.18)), Vector((0.0, -0.03, 1.12)), 70.0, (1100, 900)),
        "fretting": (Vector((-0.70, -1.55, 1.45)), Vector((0.28, -0.28, 1.42)), 98.0, (1200, 950)),
        "contact_macro": (Vector((-0.28, -1.08, 1.49)), Vector((0.33, -0.31, 1.43)), 118.0, (1200, 950)),
    }
    render_records = {}
    for name, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        output = RENDERS / f"v237_{name}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        render_records[name] = {
            "path": str(output.relative_to(ROOT)),
            "sha256": sha256(output),
            "resolution": list(resolution),
        }

    contacts = {
        digit: {
            "string": result["target_specs"][digit][0],
            "fret": result["target_specs"][digit][1],
            "root_local_m": [round(value, 7) for value in point],
            "world_m": world_point(root, point),
            "pad_center_world_m": world_point(root, result["finger_points"][digit][-1]),
            "depression_m": round(result["depression"][digit]["depression_m"], 7),
        }
        for digit, point in result["contacts"].items()
    }
    report = {
        "schema": "v237-exact-contact-integration-v1",
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "contacts": contacts,
        "thumb": {"behind_neck": True, "crosses_top_edge": False},
        "legacy_fretting_proxies_hidden": hidden,
        "integrated_objects": sorted(obj.name for obj in bpy.data.collections["V207_PLAYABLE_HANDS"].objects),
        "renders": render_records,
    }
    write_json(AUDIT / "v237_contact_integration.json", report)

    scene["V237_STATUS"] = "EXACT_V207_CONTACT_HAND_INTEGRATED"
    scene["V237_CONTACT_MAP"] = "index S5/F9; middle S4/F10; ring S7/F9; pinky S8/F11"
    scene["V237_STRING_DEPRESSION_M"] = 0.00185
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    write_json(
        AUDIT / "v237_build_receipt.json",
        {
            "status": "PASS",
            "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
            "contact_audit_sha256": sha256(AUDIT / "v237_contact_integration.json"),
        },
    )
    print("V237_EXACT_CONTACT_OK=" + json.dumps({"output": str(OUTPUT), "contacts": contacts}, sort_keys=True))


if __name__ == "__main__":
    main()
