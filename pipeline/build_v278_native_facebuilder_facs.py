"""Generate native KeenTools ARKit FACS shapes on the fitted identity head."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector

from keentools.facebuilder.settings import fb_settings
from keentools.utils.blendshapes import create_facs_blendshapes


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v221_identity_cleanup" / "Character_An_identity_cleanup_v221.blend"
STAGE = ROOT / "production_v278_native_facebuilder_facs"
OUTPUT = STAGE / "Character_An_native_facebuilder_facs_v278.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V216_REFERENCE_FITTED_HEAD"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear(keys):
    for key in keys[1:]:
        key.value = 0.0
    bpy.context.view_layer.update()


def refine_groom():
    record = {}
    hair = bpy.data.objects.get("V217_TIGHT_CURL_GROOM")
    if hair and hair.type == "CURVE":
        hair.hide_render = False
        hair.data.bevel_depth = 0.00039
        hair.data.bevel_resolution = 1
        for spline in hair.data.splines:
            last = max(1, len(spline.points) - 1)
            for index, point in enumerate(spline.points):
                t = index / last
                point.radius = (0.66 + 0.38 * math.sin(math.pi * t)) * (
                    max(0.10, (1.0 - t) / 0.25) if t > 0.75 else 1.0
                )
        material = hair.data.materials[0] if hair.data.materials else None
        if material and material.use_nodes:
            shader = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if shader:
                shader.inputs["Base Color"].default_value = (0.006, 0.003, 0.002, 1.0)
                shader.inputs["Roughness"].default_value = 0.52
                shader.inputs["Specular IOR Level"].default_value = 0.20
        record = {"object": hair.name, "splines": len(hair.data.splines), "bevel_depth_m": hair.data.bevel_depth}
    for name in ("V217_BEARD_STUBBLE", "V217_BROWS"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
    return record


def setup_scene():
    scene = bpy.context.scene
    for obj in [item for item in bpy.data.objects if item.type == "LIGHT"]:
        bpy.data.objects.remove(obj, do_unlink=True)
    target = Vector((0.0, -0.028, 1.64))
    for name, location, energy, size, color in (
        ("V278_KEY", (-0.72, -1.05, 2.07), 220.0, 0.92, (1.0, 0.91, 0.84)),
        ("V278_FILL", (0.86, -0.74, 1.76), 82.0, 0.80, (0.72, 0.82, 1.0)),
        ("V278_RIM", (0.42, 0.48, 2.02), 128.0, 0.72, (1.0, 0.72, 0.52)),
    ):
        data = bpy.data.lights.new(name + "_DATA", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light, target)
    camera_data = bpy.data.cameras.new("V278_CAMERA_DATA")
    camera = bpy.data.objects.new("V278_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    camera.location = Vector((0.0, -1.47, 1.66))
    camera.data.lens = 96.0
    point_at(camera, target)
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.006, 0.005, 0.005)
    scene.view_settings.look = "AgX - Medium High Contrast"
    return scene


def render_pose(scene, keys, label, values):
    clear(keys)
    for name, value in values.items():
        keys[name].value = value
    bpy.context.view_layer.update()
    path = RENDERS / f"v278_{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "controls": values}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    settings = fb_settings()
    if len(settings.heads) != 1:
        raise RuntimeError(f"Expected one retained FaceBuilder head, found {len(settings.heads)}")
    fb_head = settings.get_head(0)
    head = fb_head.headobj
    if not head or head.name != HEAD:
        raise RuntimeError(f"Unexpected FaceBuilder head: {head.name if head else None}")
    if head.data.shape_keys:
        while head.data.shape_keys and len(head.data.shape_keys.key_blocks):
            head.shape_key_remove(head.data.shape_keys.key_blocks[-1])
    count = create_facs_blendshapes(head, fb_head.model_scale)
    if count != 51:
        raise RuntimeError(f"Expected 51 native FACS shapes, generated {count}")
    keys = head.data.shape_keys.key_blocks
    groom = refine_groom()
    scene = setup_scene()
    # Keep the identity stack visible; suppress setup plates and unrelated meshes.
    allowed = {HEAD, "V216_EYE_L", "V216_EYE_R", "V217_TIGHT_CURL_GROOM"}
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE"} and obj.name not in allowed:
            obj.hide_render = True
    head.hide_render = False
    for name in allowed - {HEAD}:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = False
    poses = {
        "neutral": {},
        "blink": {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0},
        "jaw_open": {"jawOpen": 0.72},
        "smile": {"mouthSmileLeft": 0.92, "mouthSmileRight": 0.92, "cheekSquintLeft": 0.25, "cheekSquintRight": 0.25},
        "phoneme_o": {"mouthFunnel": 0.80, "mouthPucker": 0.35, "jawOpen": 0.16},
        "phoneme_m": {"mouthClose": 0.85, "mouthPressLeft": 0.38, "mouthPressRight": 0.38},
        "brow_raise": {"browInnerUp": 0.70, "browOuterUpLeft": 0.40, "browOuterUpRight": 0.40},
    }
    renders = {label: render_pose(scene, keys, label, values) for label, values in poses.items()}
    clear(keys)
    neutral_error = max(abs(key.value) for key in keys[1:])
    scene["V278_STATUS"] = "NATIVE_FACEBUILDER_FACS_VISUAL_REVIEW_REQUIRED"
    scene["V278_FACS_COUNT"] = count
    scene["V278_NEUTRAL_RETURN_MAX_CONTROL"] = neutral_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v278-native-facebuilder-facs-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "head": HEAD,
        "facs_count": count,
        "facs_names": [key.name for key in keys[1:]],
        "groom": groom,
        "renders": renders,
        "neutral_return_max_control": neutral_error,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v278_native_facebuilder_facs.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V278_NATIVE_FACEBUILDER_FACS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
