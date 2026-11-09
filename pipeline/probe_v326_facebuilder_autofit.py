"""Probe KeenTools FaceBuilder auto-fit with the generated photoreal front view."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
IMAGE = ROOT / "references/derived/photoreal_facebuilder_v1/character_an_front_v1.png"
STAGE = ROOT / "production_v326_photoreal_facebuilder"
OUTPUT = STAGE / "probe_front_autofit_v326.blend"
AUDIT = STAGE / "audit" / "v326_front_autofit_probe.json"


def main():
    for folder in (STAGE, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    if not hasattr(bpy.ops, "keentools_fb") or not hasattr(bpy.ops.keentools_fb, "add_head"):
        raise RuntimeError("KeenTools FaceBuilder operators are not registered")
    add_result = set(bpy.ops.keentools_fb.add_head())
    if "FINISHED" not in add_result:
        raise RuntimeError(f"FaceBuilder add_head failed: {add_result}")

    from keentools.addon_config import fb_settings
    from keentools.facebuilder.fbloader import FBLoader
    from keentools.facebuilder.pick_operator import _init_fb_detected_faces, _add_pins_to_face
    from keentools.utils.detect_faces import get_detected_faces, sort_detected_faces

    settings = fb_settings()
    headnum = settings.current_headnum
    head = settings.get_head(headnum)
    FBLoader.load_model(headnum)
    camera = FBLoader.add_new_camera_with_image(headnum, str(IMAGE))
    camnum = head.get_last_camnum()
    camera.focal = 85.0
    camera.auto_focal_estimation = False
    FBLoader.center_geo_camera_projection(headnum, camnum)
    fb = FBLoader.get_builder()
    rgba = _init_fb_detected_faces(fb, headnum, camnum)
    detected_before_sort = len(get_detected_faces())
    rectangles = sort_detected_faces()
    fit_result = _add_pins_to_face(headnum, camnum, 0) if len(rectangles) == 1 else False
    FBLoader.save_fb_serial_and_image_pathes(headnum)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)

    report = {
        "add_result": sorted(add_result),
        "headnum": headnum,
        "camnum": camnum,
        "image_shape": list(rgba.shape) if rgba is not None else None,
        "detected_faces": int(detected_before_sort),
        "rectangles": [[int(value) for value in rect] for rect in rectangles],
        "fit_result": bool(fit_result),
        "pins_count": int(camera.pins_count),
        "head_object": head.headobj.name if head.headobj else None,
        "output": str(OUTPUT),
    }
    AUDIT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("V326_FACEBUILDER_AUTOFIT_PROBE=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
