from __future__ import annotations

import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v205_wardrobe as build


def main() -> None:
    collection = bpy.data.collections["V205_WARDROBE"]
    leather = bpy.data.materials["MAT_V205_BROWN_BOOT_LEATHER"]
    elastic = bpy.data.materials["MAT_V205_BOOT_ELASTIC"]
    ramp = next((node for node in leather.node_tree.nodes if node.bl_idname == "ShaderNodeValToRGB"), None)
    if ramp is not None:
        ramp.color_ramp.elements[0].color = (0.008, 0.0015, 0.0007, 1.0)
        ramp.color_ramp.elements[1].color = (0.070, 0.015, 0.004, 1.0)
    principled = leather.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Roughness"].default_value = 0.52
        principled.inputs["Coat Weight"].default_value = 0.06

    for obj in list(bpy.data.objects):
        if obj.name.startswith(("V205_BOOT_TOE_", "V205_BOOT_FITTED_SHAFT_", "V205_BOOT_FITTED_GORE_")):
            bpy.data.objects.remove(obj, do_unlink=True)
    for prefix in ("V205_BOOT_WELT_", "V205_BOOT_PULL_TAB_", "V205_BOOT_ELASTIC_", "V205_BOOT_HEEL_"):
        for obj in bpy.data.objects:
            if obj.name.startswith(prefix):
                obj.hide_render = True
                obj.hide_viewport = True

    for side, sign in (("L", 1.0), ("R", -1.0)):
        x = sign * 0.240
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(x, -0.085, 0.100))
        toe = bpy.context.object
        toe.name = f"V205_BOOT_TOE_{side}"
        toe.scale = (0.082, 0.182, 0.068)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        build.relink(toe, collection)
        build.assign(toe, leather)
        build.smooth(toe)
        build.tag(toe, f"sculpted Chelsea toe box {side}")

        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.078, radius2=0.066, depth=0.300, location=(x, 0.026, 0.205))
        shaft = bpy.context.object
        shaft.name = f"V205_BOOT_FITTED_SHAFT_{side}"
        shaft.scale.y = 0.78
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        build.relink(shaft, collection)
        build.assign(shaft, leather)
        bevel = shaft.modifiers.new("V205_BOOT_SHAFT_EDGE", "BEVEL")
        bevel.width = 0.012
        bevel.segments = 4
        build.smooth(shaft)
        build.tag(shaft, f"fitted Chelsea ankle shaft {side}")

        gore = build.rounded_box(
            f"V205_BOOT_FITTED_GORE_{side}",
            (x + sign * 0.074, 0.020, 0.220), (0.008, 0.092, 0.110),
            collection, elastic, f"Chelsea elastic gore {side}", 0.003,
        )
        gore.rotation_euler.y = 0.0

    scene = bpy.context.scene
    scene.camera = bpy.data.objects["V205_CAM_BOOTS"]
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(ROOT / "production_v205_wardrobe" / "analysis" / "boot_rebuild_preview.png")
    Path(scene.render.filepath).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print("V205_BOOT_REBUILD_PREVIEW_OK")


if __name__ == "__main__":
    main()
