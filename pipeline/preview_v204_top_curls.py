import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

from pipeline import build_v204_groom as build


ROOT = Path(__file__).resolve().parents[1]
COUNT = 9000
SEED = 20406
HAIRLINE_COUNT = 3500
HAIRLINE_SEED = 20407


def main() -> None:
    old = bpy.data.objects.get("V204_HAIR_TOP_CURLS")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    surface = build.Surface(bpy.data.objects["V202_BODY"])
    rng = random.Random(SEED)
    strands = []
    attempts = 0
    while len(strands) < COUNT and attempts < COUNT * 30:
        attempts += 1
        y = rng.uniform(-0.078, 0.075)
        half_width = 0.087 * math.sqrt(max(0.05, 1.0 - (y / 0.115) ** 2))
        x = rng.uniform(-half_width, half_width)
        if y < 0.025 and abs(x - build.PART_X) < 0.0033:
            continue
        root, normal = surface.nearest(Vector((x, y, 1.84)))
        if root.z < 1.700:
            continue
        side = -1.0 if x < build.PART_X else 1.0
        lean = Vector((side * rng.uniform(0.0010, 0.0030), rng.uniform(-0.0005, 0.0010), -rng.uniform(0.0002, 0.0013)))
        strands.append(build.curl_strand(
            root, normal, rng.uniform(0.012, 0.020), rng.uniform(0.0010, 0.0018),
            rng.random() * math.tau, rng.uniform(0.75, 1.20), lean, 7,
        ))
    build.require(len(strands) == COUNT, f"Only generated {len(strands)} top curls")
    obj = build.make_curve_object(
        "V204_HAIR_TOP_CURLS", strands, 0.000085,
        bpy.data.materials["MAT_V204_HAIR"], bpy.data.collections["V204_GROOM_SYSTEMS"], COUNT,
    )
    build.attach_density(obj, bpy.data.node_groups["V204_GN_DENSITY_SCALP"])

    old_hairline = bpy.data.objects.get("V204_HAIRLINE_CURLS")
    if old_hairline is not None:
        bpy.data.objects.remove(old_hairline, do_unlink=True)
    hairline_rng = random.Random(HAIRLINE_SEED)
    hairline_strands = []
    for _ in range(HAIRLINE_COUNT):
        x = hairline_rng.uniform(-0.082, 0.082)
        z = 1.762 + 0.022 * (abs(x) / 0.082) ** 1.45 + hairline_rng.uniform(-0.004, 0.005)
        if abs(x - build.PART_X) < 0.0030:
            continue
        root, normal = build.face_root(surface, x, z, -0.145)
        side = -1.0 if x < build.PART_X else 1.0
        lean = Vector((side * hairline_rng.uniform(0.001, 0.004), 0.0, hairline_rng.uniform(0.001, 0.004)))
        hairline_strands.append(build.curl_strand(
            root, normal, hairline_rng.uniform(0.014, 0.023), hairline_rng.uniform(0.0013, 0.0022),
            hairline_rng.random() * math.tau, hairline_rng.uniform(0.85, 1.35), lean, 7,
        ))
    hairline = build.make_curve_object(
        "V204_HAIRLINE_CURLS", hairline_strands, 0.000095,
        bpy.data.materials["MAT_V204_HAIR"], bpy.data.collections["V204_GROOM_SYSTEMS"], len(hairline_strands),
    )
    build.attach_density(hairline, bpy.data.node_groups["V204_GN_DENSITY_SCALP"])

    build.configure_render()
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["V204_CAM_FRONT"]
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.cycles.samples = 20
    path = ROOT / "production_v204_groom" / "analysis" / "top_curl_distribution_preview.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"V204_TOP_CURL_PREVIEW_OK path={path.relative_to(ROOT)} roots={COUNT}")


if __name__ == "__main__":
    main()
