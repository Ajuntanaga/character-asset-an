from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v211_clean_base/Character_An_clean_base_v211.blend"
STAGE = ROOT / "production_v212_identity"
OUTPUT = STAGE / "Character_An_identity_v212.blend"
RENDER_DIR = STAGE / "renders/clay"
AUDIT = STAGE / "audit/v212_identity_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bell(value: float, center: float, radius: float) -> float:
    return math.exp(-((value - center) / radius) ** 2)


def smooth_band(value: float, low: float, high: float, feather: float) -> float:
    if value <= low - feather or value >= high + feather:
        return 0.0
    if low <= value <= high:
        return 1.0
    if value < low:
        t = (value - (low - feather)) / feather
    else:
        t = ((high + feather) - value) / feather
    return t * t * (3.0 - 2.0 * t)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], lens: float = 85.0) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.cameras.new(name + "_DATA")
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
    obj.data.type = "PERSP"
    obj.data.lens = lens
    obj.location = location
    look_at(obj, Vector(target))
    obj["reference_locked"] = True
    return obj


def landmark(name: str, location: tuple[float, float, float]) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.012
    obj.location = location
    obj.hide_render = True
    return obj


for directory in (STAGE, RENDER_DIR, AUDIT.parent):
    directory.mkdir(parents=True, exist_ok=True)

if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

body = bpy.data.objects["V211_BODY_NEUTRAL"]
body.name = "V212_BODY_IDENTITY"
body.data = body.data.copy()
body.data.name = "V212_BODY_IDENTITY_MESH"
body["identity_source"] = "V211_BODY_NEUTRAL"
body["identity_pass"] = "analytic_reference_form_v3"

matrix = body.matrix_world.copy()
inverse = matrix.inverted()

for vertex in body.data.vertices:
    point = matrix @ vertex.co
    x, y, z = point.x, point.y, point.z

    # Reduce the generic heroic musculature to the reference's compact,
    # naturally athletic frame while preserving joint-loop topology.
    torso = smooth_band(z, 0.88, 1.47, 0.12)
    point.x *= 1.0 - 0.055 * torso
    if 0.74 < z < 1.15:
        point.x *= 0.970

    # Take the bodybuilder roundness out of the upper torso and limbs.  The
    # approved turnaround is sturdy and naturally athletic, not hypertrophic.
    upper_torso = smooth_band(z, 1.16, 1.49, 0.08) * bell(abs(x), 0.0, 0.34)
    point.y *= 1.0 - 0.055 * upper_torso
    shoulder = smooth_band(z, 1.30, 1.47, 0.08) * smooth_band(abs(x), 0.17, 0.42, 0.06)
    point.x *= 1.0 - 0.050 * shoulder
    point.y *= 1.0 - 0.045 * shoulder
    upper_arm = smooth_band(z, 0.98, 1.42, 0.10) * smooth_band(abs(x), 0.25, 0.52, 0.06)
    point.y *= 1.0 - 0.075 * upper_arm
    thigh = smooth_band(z, 0.42, 0.88, 0.10) * smooth_band(abs(x), 0.08, 0.28, 0.05)
    point.x *= 1.0 - 0.035 * thigh
    point.y *= 1.0 - 0.050 * thigh

    # The reference has a fuller neck with less hourglass taper.
    neck = bell(z, 1.49, 0.105) * bell(abs(x), 0.0, 0.12)
    point.x *= 1.0 + 0.075 * neck
    point.y *= 1.0 + 0.040 * neck

    # Compact the vertical face slightly and broaden the jaw/cheeks.
    if z > 1.505:
        face_vertical = smooth_band(z, 1.51, 1.735, 0.025)
        point.z = 1.62 + (point.z - 1.62) * (1.0 - 0.035 * face_vertical)
        jaw = bell(z, 1.588, 0.070)
        cheek = bell(z, 1.645, 0.060)
        point.x *= 1.0 + 0.035 * jaw + 0.060 * cheek

        # Keep the lower face broad but round the mandibular corners and taper
        # naturally into the chin, matching the portrait rather than a square
        # mannequin jaw.
        jaw_corner = bell(z, 1.555, 0.045) * smooth_band(abs(x), 0.045, 0.105, 0.018)
        point.x *= 1.0 - 0.045 * jaw_corner

    # Bring the ears closer to the skull and slightly reduce their height.
    ear = smooth_band(z, 1.60, 1.70, 0.018) * smooth_band(abs(x), 0.078, 0.13, 0.018)
    if ear:
        point.x *= 1.0 - 0.055 * ear
        point.z = 1.65 + (point.z - 1.65) * (1.0 - 0.055 * ear)

    front = smooth_band(-y, 0.055, 0.16, 0.025)

    # Heavier brow and slightly deeper-set, narrower eye apertures.
    brow = bell(z, 1.710, 0.026) * smooth_band(abs(x), 0.018, 0.083, 0.020) * front
    point.y -= 0.0065 * brow
    eye_zone = bell(z, 1.681, 0.026) * smooth_band(abs(x), 0.012, 0.079, 0.018) * front
    point.z = 1.681 + (point.z - 1.681) * (1.0 - 0.045 * eye_zone)

    # Broaden the bridge and alar base, add projection at the tip.
    bridge = bell(z, 1.675, 0.065) * bell(abs(x), 0.0, 0.032) * front
    nose = bell(z, 1.645, 0.055) * bell(abs(x), 0.0, 0.050) * front
    alar = bell(z, 1.625, 0.026) * bell(abs(x), 0.0, 0.042) * front
    tip = bell(z, 1.632, 0.030) * bell(abs(x), 0.0, 0.028) * front
    point.x *= 1.0 + 0.10 * bridge + 0.16 * nose + 0.24 * alar
    point.y -= 0.008 * bridge + 0.022 * nose + 0.015 * tip

    # Fuller closed lips and a shorter, less pointed chin.
    mouth = bell(z, 1.585, 0.032) * bell(abs(x), 0.0, 0.062) * front
    upper_lip = bell(z, 1.594, 0.018) * bell(abs(x), 0.0, 0.058) * front
    lower_lip = bell(z, 1.575, 0.020) * bell(abs(x), 0.0, 0.060) * front
    point.y -= 0.010 * mouth + 0.006 * upper_lip + 0.010 * lower_lip
    point.x *= 1.0 + 0.055 * mouth
    point.z = 1.585 + (point.z - 1.585) * (1.0 + 0.15 * mouth)
    chin = bell(z, 1.535, 0.040) * bell(abs(x), 0.0, 0.068) * front
    point.x *= 1.0 + 0.035 * chin
    point.z += 0.014 * chin
    point.y += 0.001 * chin

    vertex.co = inverse @ point

body.data.update()

for eye_name in ("V211_EYE_L", "V211_EYE_R"):
    eye = bpy.data.objects.get(eye_name)
    if eye is not None:
        eye.name = eye_name.replace("V211", "V212")
        eye.scale.z *= 0.96
        eye.scale.x *= 0.98

landmarks = {
    "LM_V212_CHIN": (0.0, -0.096, 1.520),
    "LM_V212_MOUTH": (0.0, -0.137, 1.585),
    "LM_V212_NOSE_TIP": (0.0, -0.153, 1.642),
    "LM_V212_EYE_L": (0.035, -0.100, 1.681),
    "LM_V212_EYE_R": (-0.035, -0.100, 1.681),
    "LM_V212_BROW": (0.0, -0.102, 1.713),
    "LM_V212_CROWN": (0.0, 0.0, 1.800),
}
for name, position in landmarks.items():
    landmark(name, position)

face_cameras = {
    "face_front": camera("CAM_V212_FACE_FRONT", (0.0, -1.25, 1.59), (0.0, -0.02, 1.59)),
    "face_left_3q": camera("CAM_V212_FACE_LEFT_3Q", (-0.72, -1.05, 1.60), (0.0, -0.02, 1.59)),
    "face_left_profile": camera("CAM_V212_FACE_LEFT_PROFILE", (-1.25, 0.0, 1.59), (0.0, -0.02, 1.59)),
}

scene = bpy.context.scene
scene["character_asset_stage"] = "V212_IDENTITY"
scene["identity_authority"] = "supplied face sheet and turnaround; V201 targets secondary"
scene["visual_gate"] = "candidate_v3_requires_reference_comparison"
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
scene.render.film_transparent = False

full_cameras = {
    "front": bpy.data.objects["CAM_V211_FRONT"],
    "back": bpy.data.objects["CAM_V211_BACK"],
    "left_profile": bpy.data.objects["CAM_V211_LEFT_PROFILE"],
    "right_profile": bpy.data.objects["CAM_V211_RIGHT_PROFILE"],
    "front_left_3q": bpy.data.objects["CAM_V211_FRONT_LEFT_3Q"],
    "front_right_3q": bpy.data.objects["CAM_V211_FRONT_RIGHT_3Q"],
}

render_manifest: dict[str, dict[str, object]] = {}
scene.render.resolution_x = 720
scene.render.resolution_y = 960
for name, cam in full_cameras.items():
    output = RENDER_DIR / f"{name}.png"
    scene.camera = cam
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    render_manifest[name] = {"path": str(output.relative_to(ROOT)), "sha256": sha256(output)}

scene.render.resolution_x = 768
scene.render.resolution_y = 768
for name, cam in face_cameras.items():
    output = RENDER_DIR / f"{name}.png"
    scene.camera = cam
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    render_manifest[name] = {"path": str(output.relative_to(ROOT)), "sha256": sha256(output)}

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)

manifest = {
    "stage": "V212_IDENTITY",
    "status": "candidate_v3_visual_review_required",
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": sha256(SOURCE),
    "blend": str(OUTPUT.relative_to(ROOT)),
    "blend_sha256": sha256(OUTPUT),
    "topology": {"vertices": len(body.data.vertices), "polygons": len(body.data.polygons)},
    "landmarks": {name: list(position) for name, position in landmarks.items()},
    "renders": render_manifest,
    "visual_checks": [
        "compact broad face and rounded jaw",
        "heavier brow and smaller hooded eye aperture",
        "broader projected nose and alar base",
        "full closed lips and shortened chin",
        "reference-like neck and non-heroic body proportions",
    ],
}
AUDIT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

result = {
    "status": "V212_IDENTITY_CANDIDATE_V3_BUILT",
    "blend": str(OUTPUT),
    "blend_sha256": manifest["blend_sha256"],
    "renders": sorted(render_manifest),
    "visual_gate": scene["visual_gate"],
}
print("V212_IDENTITY_CANDIDATE_V3_BUILT", result)
