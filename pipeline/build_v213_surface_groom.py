from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v204_groom as groom


SOURCE = ROOT / "production_v212_identity/Character_An_identity_v212.blend"
STAGE = ROOT / "production_v213_surface_groom"
OUTPUT = STAGE / "Character_An_surface_groom_v213.blend"
RENDER_DIR = STAGE / "renders/lookdev"


def material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return value


def skin_material() -> bpy.types.Material:
    value = bpy.data.materials.get("MAT_V213_SKIN") or bpy.data.materials.new("MAT_V213_SKIN")
    value.use_nodes = True
    nodes, links = value.node_tree.nodes, value.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "V213_SKIN_PRINCIPLED"
    bsdf.subsurface_method = "RANDOM_WALK"
    bsdf.inputs["Base Color"].default_value = (0.155, 0.050, 0.022, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Subsurface Weight"].default_value = 0.085
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.43, 0.22)
    bsdf.inputs["Subsurface Scale"].default_value = 0.0013
    bsdf.inputs["Specular IOR Level"].default_value = 0.28
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 185.0
    noise.inputs["Detail"].default_value = 5.5
    noise.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.00018
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    value["surface_contract"] = "brown skin random-walk SSS with sub-millimeter pore breakup"
    return value


def assign_single(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def eye_disc(name: str, center: Vector, radius: float, depth: float, mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(center.x, center.y - 0.0121, center.z))
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.scale = (radius, depth, radius)
    assign_single(obj, mat)
    return obj


def scalp_substrate(body: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    matrix = body.matrix_world
    selected = []
    used = set()
    for polygon in body.data.polygons:
        center = matrix @ polygon.center
        hairline = 1.726 if center.y < 0.0 else 1.635
        side_floor = 1.685 + max(0.0, abs(center.x) - 0.075) * 1.6
        if center.z >= max(hairline, side_floor) and abs(center.x) < 0.101 and not (center.y < -0.055 and center.z < 1.748):
            indices = tuple(polygon.vertices)
            selected.append(indices)
            used.update(indices)
    remap = {old: new for new, old in enumerate(sorted(used))}
    vertices = [matrix @ body.data.vertices[old].co for old in sorted(used)]
    faces = [tuple(remap[index] for index in face) for face in selected]
    mesh = bpy.data.meshes.new("V213_SCALP_SUBSTRATE_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new("V213_SCALP_SUBSTRATE", mesh)
    bpy.context.scene.collection.objects.link(obj)
    assign_single(obj, mat)
    solidify = obj.modifiers.new("V213_SCALP_EMERGENCE", "SOLIDIFY")
    solidify.thickness = 0.0012
    solidify.offset = 1.0
    return obj


def nearest_face(surface: groom.Surface, x: float, z: float) -> tuple[Vector, Vector]:
    return surface.nearest(Vector((x, -0.13, z)))


def render(name: str, camera: bpy.types.Object, size: tuple[int, int]) -> None:
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


for directory in (STAGE, RENDER_DIR, STAGE / "audit", STAGE / "delivery"):
    directory.mkdir(parents=True, exist_ok=True)

# Always reload the protected source so a failed interactive attempt cannot
# leak partially-created operator objects into the next deterministic build.
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

body = bpy.data.objects["V212_BODY_IDENTITY"]
assign_single(body, skin_material())

eye_white = material("MAT_V213_SCLERA", (0.72, 0.62, 0.54, 1.0), 0.30)
eye_white.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.035
iris = material("MAT_V213_IRIS", (0.055, 0.018, 0.006, 1.0), 0.23)
pupil = material("MAT_V213_PUPIL", (0.001, 0.0005, 0.0002, 1.0), 0.16)
for eye_name in ("V212_EYE_L", "V212_EYE_R"):
    if eye_name in bpy.data.objects:
        eye = bpy.data.objects[eye_name]
        assign_single(eye, eye_white)
        center = eye.matrix_world.translation
        eye_disc(eye_name.replace("EYE", "IRIS"), center, 0.0058, 0.0010, iris)
        eye_disc(eye_name.replace("EYE", "PUPIL"), center, 0.0025, 0.0008, pupil).location.y -= 0.0007

surface = groom.Surface(body)
collection = bpy.data.collections.get("V213_GROOM") or bpy.data.collections.new("V213_GROOM")
if collection.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(collection)
hair = groom.hair_material("MAT_V213_HAIR", 0.94, 0.50, (0.0022, 0.0014, 0.0009, 1.0))
facial = groom.hair_material("MAT_V213_FACIAL_HAIR", 0.91, 0.55, (0.0032, 0.0020, 0.0012, 1.0))
scalp_substrate(body, hair)

scalp_specs = (
    ("V213_HAIR_UNDERCOAT", 3800, 21300, 0.0055, 0.00100, 0.70, 0.000095),
    ("V213_HAIR_CURLS", 2600, 21301, 0.0125, 0.00280, 1.28, 0.000125),
    ("V213_HAIR_CLUMPS", 900, 21302, 0.0160, 0.00320, 1.42, 0.000140),
)
for name, count, seed, length, radius, turns, bevel in scalp_specs:
    rng = random.Random(seed)
    strands = []
    for root, normal, phase in groom.scalp_roots(surface, count, seed):
        side = -1.0 if root.x < groom.PART_X else 1.0
        lean = Vector((side * rng.uniform(0.001, 0.0045), rng.uniform(-0.0015, 0.001), -rng.uniform(0.0, 0.002)))
        strands.append(groom.curl_strand(root, normal, length * rng.uniform(0.82, 1.20), radius, phase, turns, lean))
    groom.make_curve_object(name, strands, bevel, hair, collection, count)

beard_strands = []
for root, normal, phase, length in groom.beard_roots(surface, 1100, 21310):
    beard_strands.append(groom.short_strand(root, normal, length * 0.78, Vector((0.0, 0.0, -length * 0.28)), phase, 5))
groom.make_curve_object("V213_BEARD", beard_strands, 0.000040, facial, collection, 1100)

for side, label, seed in ((1, "L", 21320), (-1, "R", 21321)):
    rng = random.Random(seed)
    strands = []
    for _ in range(150):
        x = side * rng.uniform(0.008, 0.047)
        z = 1.607 + rng.uniform(-0.006, 0.006) - 0.035 * abs(x)
        root, normal = nearest_face(surface, x, z)
        strands.append(groom.short_strand(root, normal, 0.0065, Vector((side * 0.0035, 0.0, -0.002)), rng.random() * 6.283, 5))
    groom.make_curve_object(f"V213_MUSTACHE_{label}", strands, 0.000040, facial, collection, 150)

brow_strands = []
rng = random.Random(21330)
for side in (-1, 1):
    for _ in range(110):
        x = side * rng.uniform(0.020, 0.065)
        t = (abs(x) - 0.020) / 0.045
        z = 1.706 + 0.009 * (1.0 - (2.0 * t - 1.0) ** 2) + rng.uniform(-0.0018, 0.0018)
        root, normal = nearest_face(surface, x, z)
        brow_strands.append(groom.short_strand(root, normal, 0.0063, Vector((side * 0.0032, 0.0, 0.0015)), rng.random() * 6.283, 4))
groom.make_curve_object("V213_BROWS", brow_strands, 0.000045, facial, collection, 220)

scene = bpy.context.scene
scene["character_asset_stage"] = "V213_SURFACE_GROOM"
scene["source_checkpoint"] = "V212_IDENTITY_CANDIDATE_V2"
scene["groom_reference"] = "short dense curl, character-left part, close beard, central mustache gap"
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
scene.view_settings.look = "AgX - Medium High Contrast"

render("face_front", bpy.data.objects["CAM_V212_FACE_FRONT"], (768, 768))
render("face_left_3q", bpy.data.objects["CAM_V212_FACE_LEFT_3Q"], (768, 768))
render("face_left_profile", bpy.data.objects["CAM_V212_FACE_LEFT_PROFILE"], (768, 768))
render("full_front", bpy.data.objects["CAM_V211_FRONT"], (720, 960))

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
(STAGE / "audit/v213_manifest.json").write_text(json.dumps({
    "stage": "V213_SURFACE_GROOM",
    "source": str(SOURCE.relative_to(ROOT)),
    "output": str(OUTPUT.relative_to(ROOT)),
    "groom_systems": [obj.name for obj in bpy.data.objects if obj.name.startswith("V213_") and obj.type == "CURVE"],
    "renders": [str(path.relative_to(ROOT)) for path in sorted(RENDER_DIR.glob("*.png"))],
}, indent=2) + "\n", encoding="utf-8")
print("V213_SURFACE_GROOM_CANDIDATE_BUILT", {"output": str(OUTPUT), "curves": len([obj for obj in bpy.data.objects if obj.name.startswith("V213_") and obj.type == "CURVE"])})
