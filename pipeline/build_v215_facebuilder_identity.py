"""Build the V215 reference-fitted FaceBuilder identity head in live Blender.

Run only after the matching KeenTools Core is installed.  The three inputs are
neutral crops from the authoritative facial sheet; expression panels are not
used as identity evidence.
"""

from pathlib import Path

import bpy

from keentools.addon_config import fb_settings
from keentools.blender_independent_packages import pykeentools_loader
from keentools.facebuilder.fbloader import FBLoader
from keentools.facebuilder.pick_operator import (
    _init_fb_detected_faces,
)
from keentools.facebuilder.utils.exif_reader import auto_setup_camera_from_exif, read_exif_to_camera
from keentools.utils.coords import update_head_mesh_non_neutral
from keentools.utils.detect_faces import get_detected_faces
from keentools.utils.focal_length import configure_focal_mode_and_fixes


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
REF_DIR = ROOT / "production_v212_identity" / "facebuilder_refs"
OUT_DIR = ROOT / "production_v215_facebuilder_identity"
OUT_BLEND = OUT_DIR / "Character_An_facebuilder_identity_v215.blend"

REFERENCE_PATHS = (
    REF_DIR / "facebuilder_front_neutral.png",
    REF_DIR / "facebuilder_left_profile_neutral.png",
    REF_DIR / "facebuilder_left_3q_neutral.png",
)


def require_inputs() -> None:
    missing = [str(path) for path in REFERENCE_PATHS if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing FaceBuilder references: {missing}")


def clear_previous_facebuilder_heads() -> None:
    settings = fb_settings()
    for head in list(settings.heads):
        for camera in list(head.cameras):
            camobj = camera.camobj
            if camobj and camobj.name in bpy.data.objects:
                bpy.data.objects.remove(camobj, do_unlink=True)
        obj = head.headobj
        if obj and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    settings.heads.clear()
    settings.current_headnum = -1


def add_reference_camera(headnum: int, path: Path) -> int:
    head = fb_settings().get_head(headnum)
    camera = FBLoader.add_new_camera_with_image(headnum, str(path))
    camnum = head.get_last_camnum()
    read_exif_to_camera(headnum, camnum, str(path))
    camera.orientation = camera.exif.orientation
    auto_setup_camera_from_exif(camera)
    FBLoader.center_geo_camera_projection(headnum, camnum)
    return camnum


def fit_camera(headnum: int, camnum: int) -> None:
    settings = fb_settings()
    settings.current_headnum = headnum
    settings.current_camnum = camnum
    head = settings.get_head(headnum)
    if not FBLoader.load_model(headnum):
        raise RuntimeError(f"FaceBuilder model failed to load for head {headnum}")
    builder = FBLoader.get_builder()
    image = _init_fb_detected_faces(builder, headnum, camnum)
    if image is None:
        raise RuntimeError(f"Face detection could not load camera {camnum}")
    faces = get_detected_faces()
    if len(faces) != 1:
        raise RuntimeError(
            f"Expected exactly one detected face in camera {camnum}, got {len(faces)}"
        )
    camera = head.get_camera(camnum)
    keyframe = camera.get_keyframe()
    builder.set_use_emotions(head.should_use_emotions())
    configure_focal_mode_and_fixes(builder, head)
    result = builder.detect_face_pose(keyframe, faces[0])
    if not result:
        raise RuntimeError(f"Automatic FaceBuilder fitting failed for camera {camnum}")
    builder.remove_pins(keyframe)
    builder.add_preset_pins_and_solve(keyframe)
    update_head_mesh_non_neutral(builder, head)
    FBLoader.update_camera_pins_count(headnum, camnum)
    FBLoader.update_all_camera_positions(headnum)
    FBLoader.update_all_camera_focals(headnum)
    FBLoader.save_fb_serial_and_image_pathes(headnum)
    if head.get_camera(camnum).pins_count <= 0:
        raise RuntimeError(f"Camera {camnum} has no solved pins")


def main() -> None:
    require_inputs()
    core_installed, core_status = pykeentools_loader.installation_status(
        force_recheck=True
    )
    if not core_installed:
        raise RuntimeError(f"KeenTools Core is unavailable: {core_status}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_previous_facebuilder_heads()

    result = bpy.ops.keentools_fb.add_head()
    if "FINISHED" not in result:
        raise RuntimeError(f"FaceBuilder head creation failed: {result}")

    settings = fb_settings()
    headnum = settings.current_headnum
    head = settings.get_head(headnum)
    head.headobj.name = "V215_FACEBUILDER_IDENTITY_HEAD"

    camera_numbers = [add_reference_camera(headnum, path) for path in REFERENCE_PATHS]
    FBLoader.save_fb_serial_and_image_pathes(headnum)
    for camnum in camera_numbers:
        fit_camera(headnum, camnum)

    FBLoader.save_fb_serial_and_image_pathes(headnum)
    head.headobj["v215_reference_paths"] = [str(path) for path in REFERENCE_PATHS]
    head.headobj["v215_camera_count"] = len(camera_numbers)
    head.headobj["v215_fit_status"] = "AUTO_FIT_ALL_NEUTRAL_VIEWS"
    bpy.context.scene["V215_FACEBUILDER_IDENTITY_STATUS"] = "AUTO_FIT_ALL_NEUTRAL_VIEWS"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print({
        "status": "ok",
        "output": str(OUT_BLEND),
        "head": head.headobj.name,
        "cameras": len(camera_numbers),
        "pins": [head.get_camera(i).pins_count for i in camera_numbers],
    })


main()
