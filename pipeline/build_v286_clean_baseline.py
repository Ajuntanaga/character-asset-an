"""Promote the best anatomical wardrobe without detached experimental details."""

from pathlib import Path
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
sys.path.insert(0, str(ROOT / "pipeline"))
from build_v285_corrected_wardrobe import material, point_at, render, sha, smooth_first  # noqa: E402

SOURCE = ROOT / "production_v283_anatomical_wardrobe" / "Character_An_anatomical_wardrobe_v283.blend"
STAGE = ROOT / "production_v286_clean_baseline"
OUTPUT = STAGE / "Character_An_clean_baseline_v286.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    for name in (
        "V283_BOOT_SOLE_L",
        "V283_BOOT_SOLE_R",
        "V279_ORAL_CAVITY_TEETH_TONGUE",
        "V280_DRIVEN_ORAL_CAVITY",
        "V280_UPPER_TEETH",
    ):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    jacket = bpy.data.objects["V283_FITTED_DENIM_JACKET"]
    shirt = bpy.data.objects["V283_TAILORED_SHIRT"]
    trousers = bpy.data.objects["V283_TAILORED_TROUSERS"]
    boots = bpy.data.objects["V283_CHELSEA_BOOT_UPPERS"]
    denim = material("V286_SMOKED_INDIGO_DENIM", (.009, .014, .021), (.050, .073, .102), .70, 135.0)
    floral = material("V286_DARK_FLORAL", (.012, .002, .004), (.26, .038, .012), .62, 18.0)
    wool = material("V286_BLACK_WOOL", (.005, .006, .008), (.026, .030, .038), .77, 120.0)
    leather = material("V286_CHESTNUT_LEATHER", (.022, .005, .002), (.14, .030, .007), .40, 30.0)
    for obj, mat in ((jacket, denim), (shirt, floral), (trousers, wool), (boots, leather)):
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    smooth_first(jacket, .32, 3)
    smooth_first(shirt, .18, 2)
    smooth_first(trousers, .16, 2)
    smooth_first(boots, .55, 7)
    for vertex in trousers.data.vertices:
        axis = .093 if vertex.co.x >= 0 else -.093
        vertex.co.x = axis + (vertex.co.x - axis) * 1.055
        vertex.co.y = .005 + (vertex.co.y - .005) * 1.04
    scene = bpy.context.scene
    camera = bpy.data.objects["V283_FULL_CAMERA"]
    camera.name = "V286_FULL_CAMERA"
    camera.location = Vector((0.0, -5.25, 1.00))
    point_at(camera, Vector((0.0, 0.0, .93)))
    renders = {"front": render(scene, camera, RENDERS / "v286_clean_front.png")}
    camera.location = Vector((-3.0, -4.25, 1.12))
    point_at(camera, Vector((0.0, 0.0, .98)))
    renders["three_quarter"] = render(scene, camera, RENDERS / "v286_clean_three_quarter.png")
    scene["V286_STATUS"] = "BEST_CLEAN_WARDROBE_BASELINE"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v286-clean-baseline-v1",
        "status": "BEST_CLEAN_WARDROBE_BASELINE",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v286_clean_baseline.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V286_CLEAN_BASELINE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
