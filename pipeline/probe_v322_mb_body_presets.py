"""Bounded silhouette comparison for the corrected MB male foundation."""

from pathlib import Path
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
CHARMORPH_PARENT = ROOT / "third_party" / "charmorph" / "v0.4.0-3"
RENDERS = ROOT / "production_v322_character_rebuild" / "renders" / "body_preset_probe"
AUDIT = ROOT / "production_v322_character_rebuild" / "audit" / "v322_body_preset_probe.json"
PRESETS = ("type_lightbody", "type_slender01")


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lower, upper


def main():
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(CHARMORPH_PARENT))
    bpy.ops.preferences.addon_refresh()
    bpy.ops.preferences.addon_enable(module="CharMorph")
    from CharMorph.common import manager

    ui = bpy.context.window_manager.charmorph_ui
    ui.base_model = "mb_male"
    ui.alt_topo = "<Base>"
    ui.material_mode = "NS"
    ui.material_local = True
    ui.tex_downscale = "UL"
    ui.use_sk = False
    ui.import_morphs = False
    ui.import_expressions = False
    ui.import_cursor_z = False
    bpy.ops.charmorph.import_char()
    body = bpy.context.view_layer.objects.active
    body.name = "V322_PRESET_PROBE_BODY"
    morpher = manager.morpher
    morpher.set_L1("Latin", True)
    morpher.update_presets()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = bpy.data.worlds.new("V322_PRESET_WORLD")
    scene.world.color = (0.010, 0.012, 0.016)
    for name, location, energy, size in (
        ("KEY", (-2.4, -3.0, 3.8), 920.0, 2.4),
        ("FILL", (2.5, -1.4, 2.5), 440.0, 2.2),
        ("RIM", (0.0, 2.4, 3.2), 720.0, 1.8),
    ):
        data = bpy.data.lights.new(f"V322_PRESET_{name}_DATA", "AREA")
        data.energy = energy
        data.size = size
        light = bpy.data.objects.new(f"V322_PRESET_{name}", data)
        scene.collection.objects.link(light)
        light.location = location
        aim(light, Vector((0.0, 0.0, 1.0)))
    camera_data = bpy.data.cameras.new("V322_PRESET_CAMERA_DATA")
    camera = bpy.data.objects.new("V322_PRESET_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.lens = 72.0
    camera.location = (0.0, -3.45, 1.0)
    aim(camera, Vector((0.0, 0.0, 1.0)))

    records = {}
    for preset_name in PRESETS:
        preset = morpher.presets[preset_name]
        morpher.apply_morph_data(preset, False)
        bpy.context.view_layer.update()
        lower, upper = bounds(body)
        height = upper.z - lower.z
        factor = 1.8 / height
        body.scale = (factor,) * 3
        bpy.context.view_layer.update()
        lower, upper = bounds(body)
        body.location.z -= lower.z
        bpy.context.view_layer.update()
        path = RENDERS / f"v322_{preset_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        lower, upper = bounds(body)
        records[preset_name] = {
            "path": str(path.relative_to(ROOT)),
            "height_m": upper.z - lower.z,
            "width_m": upper.x - lower.x,
            "depth_m": upper.y - lower.y,
        }
        body.scale = (1.0,) * 3
        body.location = (0.0, 0.0, 0.0)
    AUDIT.write_text(json.dumps({"schema": "v322-body-preset-probe-v1", "presets": records}, indent=2, sort_keys=True) + "\n")
    print("V322_BODY_PRESET_PROBE=" + json.dumps(records, sort_keys=True))


if __name__ == "__main__":
    main()
