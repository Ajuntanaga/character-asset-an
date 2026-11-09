"""Build a three-view photoreal FaceBuilder head from the locked identity."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
REF_DIR = ROOT / "references" / "derived" / "photoreal_facebuilder_v1"
IMAGES = (
    REF_DIR / "character_an_front_v1.png",
    REF_DIR / "character_an_three_quarter_v1.png",
    REF_DIR / "character_an_profile_v1.png",
)
STAGE = ROOT / "production_v326_photoreal_facebuilder"
OUTPUT = STAGE / "Character_An_photoreal_head_v326.blend"
TEXTURE = STAGE / "textures" / "Character_An_photoreal_head_basecolor_v326.png"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v326_photoreal_facebuilder.json"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    hi = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lo, hi


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens=100.0):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def setup_render(head):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.012, 0.014, 0.018)
    lo, hi = bounds(head)
    center = (lo + hi) * 0.5
    size = hi - lo
    for name, offset, energy, color, area_size in (
        ("KEY", Vector((-size.x * 3.1, -size.y * 4.6, size.z * 1.5)), 380.0, (1.0, 0.96, 0.92), 1.2),
        ("FILL", Vector((size.x * 3.0, -size.y * 2.5, size.z * 0.8)), 145.0, (0.80, 0.89, 1.0), 1.4),
        ("RIM", Vector((size.x * 0.5, size.y * 4.0, size.z * 1.3)), 190.0, (0.72, 0.80, 1.0), 1.0),
    ):
        data = bpy.data.lights.new("V326_" + name + "_DATA", "AREA")
        data.energy = energy
        data.color = color
        data.size = area_size
        light = bpy.data.objects.new("V326_" + name, data)
        scene.collection.objects.link(light)
        light.location = center + offset
        aim(light, center)
    camera_data = bpy.data.cameras.new("V326_CAMERA_DATA")
    camera = bpy.data.objects.new("V326_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    camera.data.dof.use_dof = False
    return scene, camera, center, size


def main():
    for folder in (STAGE, TEXTURE.parent, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    from keentools.addon_config import fb_settings
    from keentools.facebuilder.fbloader import FBLoader
    from keentools.facebuilder.pick_operator import _init_fb_detected_faces, _add_pins_to_face
    from keentools.facebuilder.facebuilder_acts import solve_head
    from keentools.utils.detect_faces import get_detected_faces, sort_detected_faces
    from keentools.utils.materials import bake_tex, show_texture_in_mat, assign_material_to_object

    result = set(bpy.ops.keentools_fb.add_head())
    if "FINISHED" not in result:
        raise RuntimeError(f"FaceBuilder add_head failed: {result}")
    settings = fb_settings()
    headnum = settings.current_headnum
    head = settings.get_head(headnum)
    FBLoader.load_model(headnum)
    view_records = []
    for path in IMAGES:
        camera = FBLoader.add_new_camera_with_image(headnum, str(path))
        camnum = head.get_last_camnum()
        camera.focal = 85.0
        camera.auto_focal_estimation = False
        camera.use_in_tex_baking = True
        FBLoader.center_geo_camera_projection(headnum, camnum)
        fb = FBLoader.get_builder()
        rgba = _init_fb_detected_faces(fb, headnum, camnum)
        detected = len(get_detected_faces())
        rectangles = sort_detected_faces()
        fit = _add_pins_to_face(headnum, camnum, 0) if len(rectangles) == 1 else False
        view_records.append({
            "image": str(path.relative_to(ROOT)),
            "image_sha256": sha(path),
            "camera": camnum,
            "image_shape": list(rgba.shape) if rgba is not None else None,
            "detected_faces": int(detected),
            "fit": bool(fit),
            "pins": int(camera.pins_count),
            "rectangles": [[int(value) for value in rect] for rect in rectangles],
        })
    fitted = [record for record in view_records if record["fit"]]
    if len(fitted) < 2:
        raise RuntimeError(f"Fewer than two FaceBuilder views fitted: {view_records}")
    solve_head(headnum)
    FBLoader.save_fb_serial_and_image_pathes(headnum)

    settings.tex_width = 4096
    settings.tex_height = 4096
    settings.tex_face_angles_affection = 75.0
    settings.tex_uv_expand_percents = 15.0
    settings.tex_back_face_culling = True
    settings.tex_equalize_brightness = True
    settings.tex_equalize_colour = True
    settings.tex_fill_gaps = True
    texture_name = head.preview_texture_name()
    bake_status = bake_tex(headnum, texture_name)
    if not bake_status.success:
        raise RuntimeError(f"FaceBuilder texture bake failed: {bake_status.error_message}")
    texture = bpy.data.images[texture_name]
    texture.filepath_raw = str(TEXTURE)
    texture.file_format = "PNG"
    texture.save()
    material = show_texture_in_mat(texture_name, head.preview_material_name())
    assign_material_to_object(head.headobj, material)

    head_obj = head.headobj
    bpy.ops.object.select_all(action="DESELECT")
    head_obj.select_set(True)
    bpy.context.view_layer.objects.active = head_obj
    facs_result = set(bpy.ops.keentools_fb.create_blendshapes())
    shape_count = len(head_obj.data.shape_keys.key_blocks) - 1 if head_obj.data.shape_keys else 0
    if "FINISHED" not in facs_result or shape_count != 51:
        raise RuntimeError(f"FACS generation failed: {facs_result}, count={shape_count}")
    head_obj.name = "V326_PHOTOREAL_FACEBUILDER_HEAD"
    head_obj.data.name = "V326_PHOTOREAL_FACEBUILDER_HEAD_MESH"
    for polygon in head_obj.data.polygons:
        polygon.use_smooth = True

    scene, camera, center, size = setup_render(head_obj)
    distance = max(size.x, size.z) * 4.2
    renders = {
        "front": render(scene, camera, RENDERS / "v326_head_front.png", center + Vector((0.0, -distance, 0.0)), center, 105.0),
        "three_quarter": render(scene, camera, RENDERS / "v326_head_three_quarter.png", center + Vector((distance * 0.42, -distance * 0.92, size.z * 0.04)), center, 100.0),
        "profile": render(scene, camera, RENDERS / "v326_head_profile.png", center + Vector((distance, 0.0, 0.0)), center, 105.0),
    }
    scene["V326_STATUS"] = "THREE_VIEW_PHOTOREAL_FACEBUILDER_VISUAL_REVIEW_REQUIRED"
    scene["V326_FACS_COUNT"] = shape_count
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    lo, hi = bounds(head_obj)
    record = {
        "schema": "v326-photoreal-facebuilder-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "views": view_records,
        "fitted_view_count": len(fitted),
        "texture": {"path": str(TEXTURE.relative_to(ROOT)), "sha256": sha(TEXTURE), "resolution": [4096, 4096]},
        "facs_result": sorted(facs_result),
        "facs_count": shape_count,
        "head_bounds": {"min": list(lo), "max": list(hi)},
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V326_PHOTOREAL_FACEBUILDER_OK=" + json.dumps({
        "fitted_view_count": len(fitted),
        "facs_count": shape_count,
        "output_sha256": record["output"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
