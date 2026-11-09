from pathlib import Path

import bpy

from pipeline import build_v204_groom as build


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    bevels = {
        "V204_HAIR_UNDERCOAT": 0.000120,
        "V204_HAIR_GUIDES": 0.000150,
        "V204_HAIR_CHILDREN_DENSE": 0.000130,
        "V204_HAIR_CHILDREN_CLUMP": 0.000160,
        "V204_HAIR_CHILDREN_FRIZZ": 0.000070,
        "V204_HAIR_FLYAWAYS": 0.000040,
        "V204_HAIR_TOP_CURLS": 0.000130,
        "V204_BEARD_GUIDES": 0.000080,
        "V204_BEARD_CHILDREN": 0.000055,
        "V204_MUSTACHE_L": 0.000070,
        "V204_MUSTACHE_R": 0.000070,
        "V204_BROWS": 0.000075,
        "V204_LASHES": 0.000035,
    }
    for name, bevel in bevels.items():
        bpy.data.objects[name].data.bevel_depth = bevel

    cap = bpy.data.objects.get("V204_SCALP_SUBSTRATE")
    if cap is not None:
        bpy.data.objects.remove(cap, do_unlink=True)

    build.configure_render()
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["V204_CAM_FRONT"]
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.cycles.samples = 20
    path = ROOT / "production_v204_groom" / "analysis" / "groom_radius_preview.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"V204_GROOM_PREVIEW_OK path={path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
