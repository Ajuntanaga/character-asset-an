"""Install the native FaceBuilder FACS mesh into the clean full-body rig."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v240_identity_clean_rig" / "Character_An_identity_clean_rig_v240.blend"
FACS_SOURCE = ROOT / "production_v278_native_facebuilder_facs" / "Character_An_native_facebuilder_facs_v278.blend"
ORAL_SOURCE = ROOT / "production_v276j_corrected_facial_controls" / "Character_An_corrected_facial_controls_v276j.blend"
STAGE = ROOT / "production_v279_facs_body_integration"
OUTPUT = STAGE / "Character_An_facs_body_integration_v279.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V216_REFERENCE_FITTED_HEAD"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def append_object(path, name):
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        if name not in source.objects:
            raise RuntimeError(f"Missing {name} in {path}")
        target.objects = [name]
    obj = target.objects[0]
    bpy.context.scene.collection.objects.link(obj)
    return obj


def replace_mesh_data(target, source):
    old = target.data
    target.data = source.data.copy()
    target.data.name = target.name + "_V279_FACS_MESH"
    bpy.data.objects.remove(source, do_unlink=True)
    if old.users == 0:
        bpy.data.meshes.remove(old)


def parent_to_head_bone(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def setup_portrait_camera(scene):
    data = bpy.data.cameras.new("V279_PORTRAIT_CAMERA_DATA")
    camera = bpy.data.objects.new("V279_PORTRAIT_CAMERA", data)
    scene.collection.objects.link(camera)
    camera.location = Vector((0.0, -1.50, 1.66))
    camera.data.lens = 96.0
    point_at(camera, Vector((0.0, -0.025, 1.64)))
    return camera


def render(scene, camera, path, x=768, y=768):
    scene.camera = camera
    scene.render.resolution_x = x
    scene.render.resolution_y = y
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def clear_facs(keys):
    for key in keys[1:]:
        key.value = 0.0
    bpy.context.view_layer.update()


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG]
    head = bpy.data.objects[HEAD]
    parent_record = {"parent": head.parent.name, "parent_type": head.parent_type, "parent_bone": head.parent_bone}

    facs_head = append_object(FACS_SOURCE, HEAD)
    facs_count = len(facs_head.data.shape_keys.key_blocks) - 1 if facs_head.data.shape_keys else 0
    if facs_count != 51 or len(facs_head.data.vertices) != len(head.data.vertices):
        raise RuntimeError(f"FACS replacement mismatch: {facs_count} shapes, {len(facs_head.data.vertices)} vertices")
    replace_mesh_data(head, facs_head)

    facs_hair = append_object(FACS_SOURCE, "V217_TIGHT_CURL_GROOM")
    hair = bpy.data.objects.get("V217_TIGHT_CURL_GROOM")
    if hair is facs_hair:
        raise RuntimeError("Expected the rig scene to retain its existing groom object")
    old_hair = hair.data
    hair.data = facs_hair.data.copy()
    bpy.data.objects.remove(facs_hair, do_unlink=True)
    if old_hair.users == 0:
        bpy.data.curves.remove(old_hair)
    hair.hide_render = False

    # Use the already seated dental/tongue asset as a first real oral cavity.
    oral = append_object(ORAL_SOURCE, "V276E_Jaw - Realistic")
    oral.name = "V279_ORAL_CAVITY_TEETH_TONGUE"
    oral.hide_render = False
    parent_to_head_bone(oral, rig)

    keys = head.data.shape_keys.key_blocks
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    portrait = setup_portrait_camera(scene)
    renders = {}
    clear_facs(keys)
    renders["portrait_neutral"] = render(scene, portrait, RENDERS / "v279_portrait_neutral.png")
    keys["mouthSmileLeft"].value = 0.9
    keys["mouthSmileRight"].value = 0.9
    keys["cheekSquintLeft"].value = 0.22
    keys["cheekSquintRight"].value = 0.22
    bpy.context.view_layer.update()
    renders["portrait_smile"] = render(scene, portrait, RENDERS / "v279_portrait_smile.png")
    clear_facs(keys)
    keys["jawOpen"].value = 0.72
    bpy.context.view_layer.update()
    renders["portrait_jaw"] = render(scene, portrait, RENDERS / "v279_portrait_jaw.png")
    clear_facs(keys)

    full_camera = bpy.data.objects.get("CAM_V211_FRONT")
    if not full_camera:
        raise RuntimeError("Missing V240 front camera")
    renders["full_body_front"] = render(scene, full_camera, RENDERS / "v279_full_body_front.png", 720, 960)
    neutral_error = max(abs(key.value) for key in keys[1:])
    scene["V279_STATUS"] = "NATIVE_FACS_BODY_INTEGRATION_VISUAL_REVIEW_REQUIRED"
    scene["V279_FACS_COUNT"] = facs_count
    scene["V279_NEUTRAL_RETURN_MAX_CONTROL"] = neutral_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v279-facs-body-integration-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "facs_source": {"path": str(FACS_SOURCE.relative_to(ROOT)), "sha256": sha(FACS_SOURCE)},
        "oral_source": {"path": str(ORAL_SOURCE.relative_to(ROOT)), "sha256": sha(ORAL_SOURCE)},
        "head": HEAD,
        "rig": RIG,
        "parenting": parent_record,
        "facs_count": facs_count,
        "oral_asset": oral.name,
        "neutral_return_max_control": neutral_error,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v279_facs_body_integration.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V279_FACS_BODY_INTEGRATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
