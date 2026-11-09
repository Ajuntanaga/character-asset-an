from __future__ import annotations

import binascii
import json
import math
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v203_skin_eyes"
SOURCE = ROOT / "production_v202_neutral_anatomy" / "ant_neutral_anatomy_v202.blend"
OUTPUT = STAGE / "ant_skin_eyes_v203.blend"
TEXTURES = STAGE / "textures"
EXPECTED_SOURCE_SHA256 = "36548545f881ceca50f7944f9562f2d9b45a09affa2bc194894d7a6597ee48be"
EXPECTED_V200_SHA256 = "42612cfbd1cbeed03c0db1eb085ea10f1ca73fe3697404ad563d1cb15599c6d1"
EXPECTED_V192_SHA256 = "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"
MACRO_GUIDE = Path("/home/ajuntanaga/.codex/generated_images/01a0f69f-f997-7582-b363-29bf5f1d74f0/exec-a2c15fd8-7b7f-4538-9490-93bacc2cd966.png")
EXPECTED_MACRO_SHA256 = "8c2315fc8b567192c69dff923cb8f285f1e7387fc01713d33a3c5f76ba3fc24b"

MAP_KINDS = ("albedo", "roughness", "pore_normal", "fine_displacement_mask")
RENDER_VIEWS = {
    "face_neutral": ("V203_CAM_FACE_NEUTRAL", (768, 768), True, "neutral"),
    "face_grazing": ("V203_CAM_FACE_GRAZING", (768, 768), True, "grazing"),
    "eye": ("V203_CAM_EYE", (768, 768), True, "neutral"),
    "lips": ("V203_CAM_LIPS", (768, 768), True, "grazing"),
    "ear": ("V203_CAM_EAR", (768, 768), True, "grazing"),
    "hand_dorsal": ("V203_CAM_HAND_DORSAL", (768, 768), True, "neutral"),
    "palm": ("V203_CAM_PALM", (768, 768), True, "neutral"),
    "nails": ("V203_CAM_NAILS", (768, 768), True, "grazing"),
    "micro_undenoised": ("V203_CAM_MICRO_UNDENOISED", (1024, 1024), False, "grazing"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def png_chunk(handle, kind: bytes, payload: bytes) -> None:
    handle.write(struct.pack(">I", len(payload)))
    handle.write(kind)
    handle.write(payload)
    handle.write(struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF))


def texture_row(kind: str, tile: int, width: int, row: int) -> np.ndarray:
    u = (np.arange(width, dtype=np.float32) + 0.5) / width
    v = (row + 0.5) / width
    phase = tile * 0.071
    low = np.sin((u * 3.1 + v * 1.7 + phase) * math.tau) * np.cos((u * 1.3 - v * 2.3) * math.tau)
    pores = np.sin((u * 183.0 + v * 137.0 + phase) * math.tau) * np.sin((u * 89.0 - v * 211.0) * math.tau)
    fine = np.sin((u * 431.0 + v * 307.0 + phase) * math.tau)
    if kind == "albedo":
        # Warm medium-brown base sampled from the lower-authority V201
        # interpretation plate, with bounded chromatic rather than lighting
        # variation. The supplied sheets continue to govern identity.
        base = np.array((0.40, 0.27, 0.19), dtype=np.float32)
        variation = 1.0 + low[:, None] * np.array((0.050, 0.038, 0.025), dtype=np.float32)
        warmth = pores[:, None] * np.array((0.010, 0.004, -0.003), dtype=np.float32)
        values = np.clip(base * variation + warmth, 0.0, 1.0)
    elif kind == "roughness":
        values = np.clip(0.43 + low * 0.055 + pores * 0.025, 0.28, 0.62)[:, None]
    elif kind == "pore_normal":
        nx = 0.022 * np.sin((u * 257.0 + v * 193.0 + phase) * math.tau)
        ny = 0.022 * np.cos((u * 229.0 - v * 271.0 + phase) * math.tau)
        nz = np.sqrt(np.clip(1.0 - nx * nx - ny * ny, 0.0, 1.0))
        values = np.stack((0.5 + nx * 0.5, 0.5 + ny * 0.5, 0.5 + nz * 0.5), axis=1)
    else:
        values = np.clip(0.5 + pores * 0.030 + fine * 0.012 + low * 0.018, 0.40, 0.60)[:, None]
    return np.round(values * 65535.0).astype(">u2")


def write_png16(path: Path, size: int, kind: str, tile: int, force: bool = False) -> None:
    channels = 3 if kind in {"albedo", "pore_normal"} else 1
    color_type = 2 if channels == 3 else 0
    if path.is_file() and not force:
        with path.open("rb") as handle:
            header = handle.read(26)
        if header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", header[16:24]) == (size, size) and header[24] == 16:
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        png_chunk(handle, b"IHDR", struct.pack(">IIBBBBB", size, size, 16, color_type, 0, 0, 0))
        compressor = zlib.compressobj(level=6)
        bytes_per_pixel = channels * 2
        for row in range(size):
            raw = np.frombuffer(texture_row(kind, tile, size, row).tobytes(), dtype=np.uint8).copy()
            filtered = raw.copy()
            filtered[bytes_per_pixel:] = (raw[bytes_per_pixel:].astype(np.uint16) - raw[:-bytes_per_pixel].astype(np.uint16)) & 0xFF
            data = compressor.compress(b"\x01" + filtered.tobytes())
            if data:
                png_chunk(handle, b"IDAT", data)
        tail = compressor.flush()
        if tail:
            png_chunk(handle, b"IDAT", tail)
        png_chunk(handle, b"IEND", b"")


def body_tile_records(body: bpy.types.Object) -> list[dict[str, object]]:
    uv_layer = body.data.uv_layers.active
    require(uv_layer is not None, "V202 body has no UV layer")
    stats: dict[int, dict[str, object]] = {}
    for polygon in body.data.polygons:
        us = [uv_layer.data[index].uv.x for index in polygon.loop_indices]
        vs = [uv_layer.data[index].uv.y for index in polygon.loop_indices]
        u, v = math.floor(sum(us) / len(us)), math.floor(sum(vs) / len(vs))
        tile = 1001 + u + 10 * v
        record = stats.setdefault(tile, {"number": tile, "polygon_count": 0})
        record["polygon_count"] = int(record["polygon_count"]) + 1
    semantic = {
        1001: "head", 1021: "head",
        1002: "face", 1022: "face",
        1003: "hands", 1023: "hands",
        1004: "arms", 1024: "arms",
        1005: "feet", 1025: "feet",
        1006: "body", 1026: "body", 1007: "body", 1027: "body",
        1008: "legs", 1028: "legs", 1009: "legs", 1029: "legs",
        1011: "body", 1031: "body", 1012: "body", 1032: "body", 1013: "body", 1033: "body",
    }
    require(set(stats) == set(semantic), f"Unexpected occupied UDIM layout: {sorted(stats)}")
    records = []
    for tile in sorted(stats):
        records.append({**stats[tile], "semantic": semantic[tile], "resolution": 4096 if semantic[tile] in {"head", "face", "hands"} else 2048})
    return records


def create_textures(tile_records: list[dict[str, object]]) -> dict[str, object]:
    maps = []
    for kind in MAP_KINDS:
        tiles = []
        for record in tile_records:
            tile = int(record["number"])
            size = int(record["resolution"])
            filename = f"v203_skin_{kind}.{tile}.png"
            path = TEXTURES / filename
            write_png16(path, size, kind, tile)
            tiles.append({
                "number": tile,
                "semantic": record["semantic"],
                "resolution": [size, size],
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            })
        maps.append({
            "kind": kind,
            "bit_depth": 16,
            "colorspace": "sRGB" if kind == "albedo" else "Non-Color",
            "image_path_pattern": f"//textures/v203_skin_{kind}.<UDIM>.png",
            "tiles": tiles,
        })
    manifest = {
        "maps_schema": "v203-16bit-udim-v1",
        "source_uv_object": "V202_BODY",
        "occupied_tiles": [record["number"] for record in tile_records],
        "allocation": tile_records,
        "maps": maps,
        "note": "Only actually occupied production UV tiles are authored; head, face and hands are 4K, all other occupied tiles are 2K.",
    }
    write_json(STAGE / "analysis" / "v203_texture_manifest.json", manifest)
    return manifest


def load_udim_image(name: str, pattern: str, tile_records: list[dict[str, object]], colorspace: str) -> bpy.types.Image:
    existing = bpy.data.images.get(name)
    if existing:
        bpy.data.images.remove(existing)
    first = pattern.replace("<UDIM>", str(tile_records[0]["number"]))
    image = bpy.data.images.load(str(TEXTURES / first), check_existing=False)
    image.name = name
    image.source = "TILED"
    image.filepath = f"//textures/{pattern}"
    image.colorspace_settings.name = colorspace
    existing_tiles = {tile.number for tile in image.tiles}
    for record in tile_records:
        number = int(record["number"])
        if number not in existing_tiles:
            image.tiles.new(number)
    return image


def material(name: str, color: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    nodes = value.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = metallic
    return value


def assign(obj_name: str, value: bpy.types.Material) -> None:
    obj = bpy.data.objects[obj_name]
    obj.data.materials.clear()
    obj.data.materials.append(value)


def create_skin_material(tile_records: list[dict[str, object]]) -> bpy.types.Material:
    value = bpy.data.materials.get("MAT_V203_SKIN") or bpy.data.materials.new("MAT_V203_SKIN")
    value.use_nodes = True
    nodes = value.node_tree.nodes
    links = value.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.name = "V203_OUTPUT"
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.name = "V203_SKIN_PRINCIPLED"
    principled.subsurface_method = "RANDOM_WALK"
    principled.inputs["Subsurface Weight"].default_value = 0.075
    principled.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.20)
    principled.inputs["Subsurface Scale"].default_value = 0.0015
    principled.inputs["IOR"].default_value = 1.40
    principled.inputs["Specular IOR Level"].default_value = 0.24
    principled.inputs["Coat Weight"].default_value = 0.01
    principled.inputs["Coat Roughness"].default_value = 0.32
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    images = {
        kind: load_udim_image(f"IMG_V203_{kind.upper()}", f"v203_skin_{kind}.<UDIM>.png", tile_records, "sRGB" if kind == "albedo" else "Non-Color")
        for kind in MAP_KINDS
    }
    tex_nodes = {}
    for index, (kind, image) in enumerate(images.items()):
        node = nodes.new("ShaderNodeTexImage")
        node.name = {"albedo": "V203_ALBEDO", "roughness": "V203_ROUGHNESS", "pore_normal": "V203_PORE_NORMAL", "fine_displacement_mask": "V203_FINE_DISPLACEMENT"}[kind]
        node.image = image
        node.interpolation = "Linear"
        node.extension = "EXTEND"
        node.location = (-720, 260 - index * 230)
        tex_nodes[kind] = node
    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V203_NORMAL_MAP"
    normal.inputs["Strength"].default_value = 0.42
    bump = nodes.new("ShaderNodeBump")
    bump.name = "V203_MICRO_BUMP"
    bump.inputs["Strength"].default_value = 0.24
    bump.inputs["Distance"].default_value = 0.00022
    links.new(tex_nodes["albedo"].outputs["Color"], principled.inputs["Base Color"])
    links.new(tex_nodes["roughness"].outputs["Color"], principled.inputs["Roughness"])
    links.new(tex_nodes["pore_normal"].outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bump.inputs["Normal"])
    links.new(tex_nodes["fine_displacement_mask"].outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    value["texture_manifest"] = "//analysis/v203_texture_manifest.json"
    value["subsurface_mode"] = "RANDOM_WALK"
    value["microdetail_scale_m"] = 0.00035
    return value


def create_organ_materials() -> dict[str, bpy.types.Material]:
    sclera = material("MAT_V203_SCLERA", (0.72, 0.67, 0.61, 1.0), 0.34)
    sclera.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.045
    iris = material("MAT_V203_IRIS_BROWN", (0.105, 0.035, 0.012, 1.0), 0.28)
    iris_nodes = iris.node_tree.nodes
    noise = iris_nodes.get("V203_IRIS_RADIAL") or iris_nodes.new("ShaderNodeTexNoise")
    noise.name = "V203_IRIS_RADIAL"
    noise.inputs["Scale"].default_value = 38.0
    noise.inputs["Detail"].default_value = 8.0
    bump = iris_nodes.get("V203_IRIS_BUMP") or iris_nodes.new("ShaderNodeBump")
    bump.name = "V203_IRIS_BUMP"
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.00018
    iris.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    iris.node_tree.links.new(bump.outputs["Normal"], iris_nodes["Principled BSDF"].inputs["Normal"])
    pupil = material("MAT_V203_PUPIL", (0.002, 0.001, 0.0005, 1.0), 0.20)
    cornea = material("MAT_V203_CORNEA", (0.98, 0.99, 1.0, 1.0), 0.018)
    cornea_bsdf = cornea.node_tree.nodes["Principled BSDF"]
    cornea_bsdf.inputs["Transmission Weight"].default_value = 1.0
    cornea_bsdf.inputs["IOR"].default_value = 1.376
    cornea_bsdf.inputs["Coat Weight"].default_value = 0.18
    tearline = material("MAT_V203_TEARLINE", (0.88, 0.93, 0.95, 1.0), 0.012)
    tear_bsdf = tearline.node_tree.nodes["Principled BSDF"]
    tear_bsdf.inputs["Transmission Weight"].default_value = 1.0
    tear_bsdf.inputs["IOR"].default_value = 1.336
    oral = material("MAT_V203_ORAL_CAVITY", (0.055, 0.008, 0.006, 1.0), 0.48)
    teeth = material("MAT_V203_TEETH", (0.72, 0.61, 0.46, 1.0), 0.34)
    teeth.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.04
    gum = material("MAT_V203_GUM", (0.24, 0.035, 0.030, 1.0), 0.40)
    gum.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.08
    tongue = material("MAT_V203_TONGUE", (0.34, 0.055, 0.045, 1.0), 0.38)
    tongue.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.10
    nail = material("MAT_V203_NAIL", (0.42, 0.19, 0.12, 1.0), 0.30)
    nail_bsdf = nail.node_tree.nodes["Principled BSDF"]
    nail_bsdf.inputs["Subsurface Weight"].default_value = 0.055
    nail_bsdf.inputs["Coat Weight"].default_value = 0.16
    nail_bsdf.inputs["Coat Roughness"].default_value = 0.22
    lash = material("MAT_V203_LASH", (0.006, 0.003, 0.002, 1.0), 0.48)
    return {value.name: value for value in (sclera, iris, pupil, cornea, tearline, oral, teeth, gum, tongue, nail, lash)}


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return Vector(tuple(min(point[index] for point in points) for index in range(3))), Vector(tuple(max(point[index] for point in points) for index in range(3)))


def curve_arc(name: str, points: list[Vector], bevel: float, mat: bpy.types.Material, collection: bpy.types.Collection) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 4
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    curve.materials.append(mat)
    return obj


def create_eye_moisture(materials: dict[str, bpy.types.Material]) -> None:
    collection = bpy.data.collections.get("V203_EYE_DETAIL") or bpy.data.collections.new("V203_EYE_DETAIL")
    if not collection.name in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    for side in ("L", "R"):
        sclera = bpy.data.objects[f"V202_EYE_{side}_SCLERA"]
        minimum, maximum = world_bounds(sclera)
        center = (minimum + maximum) * 0.5
        rx = (maximum.x - minimum.x) * 0.44
        rz = (maximum.z - minimum.z) * 0.38
        front_y = minimum.y - 0.0005
        tear_points = [Vector((center.x + rx * t, front_y, center.z - rz * (0.46 + 0.18 * (t * t)))) for t in (-1.0, -0.66, -0.33, 0.0, 0.33, 0.66, 1.0)]
        lash_points = [Vector((center.x + rx * t, front_y - 0.0004, center.z + rz * (0.46 + 0.12 * (t * t)))) for t in (-1.0, -0.66, -0.33, 0.0, 0.33, 0.66, 1.0)]
        curve_arc(f"V203_TEARLINE_{side}", tear_points, 0.00042, materials["MAT_V203_TEARLINE"], collection)
        curve_arc(f"V203_LASH_{side}", lash_points, 0.00023, materials["MAT_V203_LASH"], collection)


def assign_lookdev(materials: dict[str, bpy.types.Material], skin: bpy.types.Material) -> None:
    assign("V202_BODY", skin)
    for side in ("L", "R"):
        assign(f"V202_EYE_{side}_SCLERA", materials["MAT_V203_SCLERA"])
        assign(f"V202_EYE_{side}_IRIS", materials["MAT_V203_IRIS_BROWN"])
        assign(f"V202_EYE_{side}_PUPIL", materials["MAT_V203_PUPIL"])
        assign(f"V202_EYE_{side}_CORNEA", materials["MAT_V203_CORNEA"])
        bpy.data.objects[f"V202_EYE_{side}_CORNEA"].hide_render = False
    for name in ("V202_LID_L_UPPER", "V202_LID_L_LOWER", "V202_LID_R_UPPER", "V202_LID_R_LOWER", "V202_TEAR_DUCT_L", "V202_TEAR_DUCT_R"):
        bpy.data.objects[name].hide_render = True
    assign("V202_ORAL_CAVITY", materials["MAT_V203_ORAL_CAVITY"])
    for name in ("V202_TEETH_UPPER", "V202_TEETH_LOWER"):
        assign(name, materials["MAT_V203_TEETH"])
    for name in ("V202_GUM_UPPER", "V202_GUM_LOWER"):
        assign(name, materials["MAT_V203_GUM"])
    assign("V202_TONGUE", materials["MAT_V203_TONGUE"])
    for obj in bpy.data.objects:
        if obj.name.startswith("V202_NAIL_"):
            assign(obj.name, materials["MAT_V203_NAIL"])


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(name: str, source_name: str, location: tuple[float, float, float], target: tuple[float, float, float], scale: float) -> bpy.types.Object:
    source = bpy.data.objects[source_name]
    camera_data = source.data.copy()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = scale
    obj = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, Vector(target))
    return obj


def create_cameras() -> dict[str, bpy.types.Object]:
    cameras = {
        "V203_CAM_FACE_NEUTRAL": make_camera("V203_CAM_FACE_NEUTRAL", "V202_CAM_HEAD_FRONT", (0.0, -2.2, 1.685), (0.0, 0.0, 1.685), 0.31),
        "V203_CAM_FACE_GRAZING": make_camera("V203_CAM_FACE_GRAZING", "V202_CAM_HEAD_THREE_QUARTER", (1.7, -1.7, 1.69), (0.0, 0.0, 1.68), 0.31),
        "V203_CAM_EYE": make_camera("V203_CAM_EYE", "V202_CAM_HEAD_FRONT", (-0.037, -2.2, 1.672), (-0.037, 0.0, 1.672), 0.105),
        "V203_CAM_LIPS": make_camera("V203_CAM_LIPS", "V202_CAM_HEAD_FRONT", (0.0, -2.2, 1.59), (0.0, 0.0, 1.59), 0.105),
        "V203_CAM_EAR": make_camera("V203_CAM_EAR", "V202_CAM_HEAD_PROFILE", (2.2, 0.0, 1.665), (0.0, 0.0, 1.665), 0.19),
        "V203_CAM_HAND_DORSAL": make_camera("V203_CAM_HAND_DORSAL", "V202_CAM_HAND_L", (0.44, -2.2, 0.89), (0.44, 0.0, 0.89), 0.29),
        "V203_CAM_PALM": make_camera("V203_CAM_PALM", "V202_CAM_HAND_L", (0.44, 2.2, 0.89), (0.44, 0.0, 0.89), 0.29),
        "V203_CAM_NAILS": make_camera("V203_CAM_NAILS", "V202_CAM_HAND_L", (0.44, -2.2, 0.89), (0.44, 0.0, 0.89), 0.18),
        "V203_CAM_MICRO_UNDENOISED": make_camera("V203_CAM_MICRO_UNDENOISED", "V202_CAM_HEAD_FRONT", (-0.065, -2.2, 1.635), (-0.065, 0.0, 1.635), 0.075),
    }
    return cameras


def create_reference_manifest(cameras: dict[str, bpy.types.Object]) -> dict[str, object]:
    targets = STAGE / "targets"
    targets.mkdir(parents=True, exist_ok=True)
    require(MACRO_GUIDE.is_file() and sha256(MACRO_GUIDE) == EXPECTED_MACRO_SHA256, "V203 macro guide missing or changed")
    macro_target = targets / "v203_photoreal_macro_reference_v1.png"
    shutil.copy2(MACRO_GUIDE, macro_target)
    reference_collection = bpy.data.collections.get("V202_REFERENCE_GUIDES")
    require(reference_collection is not None, "Missing inherited reference collection")
    reference_collection.name = "V203_PHOTO_REFERENCES"
    reference_collection.hide_render = True

    entries = []
    for image in sorted((image for image in bpy.data.images if image.name.startswith("V201_REFERENCE_")), key=lambda image: image.name):
        path = Path(bpy.path.abspath(image.filepath)).resolve()
        rel = str(path.relative_to(ROOT))
        if "v201_m3_contact_diagram" in rel:
            authority, domain, camera = "analytic_m3", "hand_contact", "V203_CAM_HAND_DORSAL"
        elif rel.startswith("references/"):
            authority = "supplied"
            if "/facial/" in rel:
                domain, camera = "face_identity", "V203_CAM_FACE_NEUTRAL"
            elif "/hands/" in rel:
                domain, camera = "hands", "V203_CAM_HAND_DORSAL"
            elif "/props/" in rel:
                domain, camera = "prop_context", "V203_CAM_NAILS"
            else:
                domain, camera = "character_identity", "V203_CAM_FACE_NEUTRAL"
        else:
            authority = "generated_guidance"
            if "hand" in rel:
                domain, camera = "hands", "V203_CAM_HAND_DORSAL"
            elif "guitar" in rel:
                domain, camera = "prop_context", "V203_CAM_NAILS"
            else:
                domain, camera = "photoreal_interpretation", "V203_CAM_FACE_NEUTRAL"
        entries.append({"path": rel, "sha256": sha256(path), "authority": authority, "domain": domain, "matched_camera": camera})
    entries.append({
        "path": str(macro_target.relative_to(ROOT)),
        "sha256": sha256(macro_target),
        "authority": "generated_guidance",
        "domain": "skin_eye_mouth_nail_microdetail",
        "matched_camera": "V203_CAM_MICRO_UNDENOISED",
    })
    require(len(entries) == 16, f"Expected 16 photo references, got {len(entries)}")
    manifest = {
        "schema": "v203-photo-reference-workflow-v1",
        "workflow": "SUPPLIED_FIRST_MATCHED_CAMERAS",
        "authority_order": ["supplied", "analytic_m3", "generated_guidance"],
        "references": entries,
        "matched_cameras": sorted(cameras),
    }
    write_json(STAGE / "analysis" / "v203_photo_reference_manifest.json", manifest)
    return manifest


def configure_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.04
    scene.cycles.use_denoising = True
    scene.cycles.device = "CPU"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.035, 0.035, 0.035)
    # V203 is a genuine Cycles look-development checkpoint.  V209 later raises
    # approval samples and finishes every asset-domain material.


def render_suite(cameras: dict[str, bpy.types.Object]) -> dict[str, object]:
    scene = bpy.context.scene
    configure_render()
    render_dir = STAGE / "renders" / "lookdev"
    render_dir.mkdir(parents=True, exist_ok=True)
    key = bpy.data.objects.get("V202_KEY")
    fill = bpy.data.objects.get("V202_FILL")
    rim = bpy.data.objects.get("V202_RIM")
    results = {}
    for view, (camera_name, resolution, denoised, lighting) in RENDER_VIEWS.items():
        scene.camera = cameras[camera_name]
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.cycles.use_denoising = denoised
        if key and fill and rim:
            if lighting == "grazing":
                key.data.energy, fill.data.energy, rim.data.energy = 340.0, 45.0, 285.0
                key.location = (2.1, -1.1, 2.0)
                rim.location = (-1.7, 0.4, 1.8)
            else:
                key.data.energy, fill.data.energy, rim.data.energy = 260.0, 90.0, 170.0
                key.location = (-1.4, -1.6, 2.3)
                rim.location = (1.6, 0.5, 2.0)
        path = render_dir / f"{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        require(path.is_file(), f"Missing render: {path}")
        results[view] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "camera": camera_name,
            "resolution": list(resolution),
            "renderer": "Cycles CPU",
            "denoised": denoised,
            "lighting": lighting,
        }
    scene.cycles.samples = 64
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.use_denoising = True
    scene.cycles.device = "CPU"
    return results


def main() -> None:
    require(not OUTPUT.exists(), f"Refusing to overwrite immutable checkpoint: {OUTPUT}")
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Live Blender must have accepted V202 open, got {bpy.data.filepath}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V202 source hash changed")
    require(sha256(ROOT / "ant_character_asset_final_v200.blend") == EXPECTED_V200_SHA256, "Protected V200 changed")
    require(sha256(ROOT / "ant_compact_pick_pinch_v192.blend") == EXPECTED_V192_SHA256, "Protected V192 changed")
    for path in (STAGE / "analysis", STAGE / "audit", STAGE / "delivery", STAGE / "renders" / "lookdev", TEXTURES, STAGE / "targets"):
        path.mkdir(parents=True, exist_ok=True)

    body = bpy.data.objects.get("V202_BODY")
    require(body is not None and body.type == "MESH", "Missing accepted V202 body")
    tile_records = body_tile_records(body)
    texture_manifest = create_textures(tile_records)
    skin = create_skin_material(tile_records)
    materials = create_organ_materials()
    assign_lookdev(materials, skin)
    create_eye_moisture(materials)
    cameras = create_cameras()
    reference_manifest = create_reference_manifest(cameras)

    scene = bpy.context.scene
    scene["checkpoint"] = "V203_SKIN_EYES"
    scene["source_v202_sha256"] = EXPECTED_SOURCE_SHA256
    scene["photo_reference_workflow"] = "SUPPLIED_FIRST_MATCHED_CAMERAS"
    scene["reference_authority"] = "supplied sheets > analytic M3 > generated guidance"
    scene["skin_shader"] = "Principled BSDF / Random Walk / occupied semantic UDIMs"
    scene["v203_texture_manifest"] = "//analysis/v203_texture_manifest.json"
    scene["v203_photo_reference_manifest"] = "//analysis/v203_photo_reference_manifest.json"

    render_results = render_suite(cameras)
    render_manifest = {
        "schema": "v203-render-manifest-v1",
        "checkpoint": "V203_SKIN_EYES",
        "scene_final_renderer": "Cycles CPU",
        "adaptive_sampling": True,
        "oidn_enabled_for_cycles_approval": True,
        "lookdev_note": "All V203 contact views were rendered in Cycles CPU. V209 raises approval samples and completes remaining material domains.",
        "renders": render_results,
    }
    write_json(STAGE / "audit" / "v203_render_manifest.json", render_manifest)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    # Relative paths must be authored after the file's base directory changes
    # from V202 to V203; otherwise Blender rebases them back into the source
    # stage during Save As.
    for kind in MAP_KINDS:
        image = bpy.data.images[f"IMG_V203_{kind.upper()}"]
        image.filepath = f"//textures/v203_skin_{kind}.<UDIM>.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    require(OUTPUT.is_file(), "V203 checkpoint was not saved")
    output_hash = sha256(OUTPUT)
    receipt = {
        "status": "PASS",
        "checkpoint": "V203_SKIN_EYES",
        "blender_version": bpy.app.version_string,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "texture_manifest": {"path": str((STAGE / "analysis" / "v203_texture_manifest.json").relative_to(ROOT)), "sha256": sha256(STAGE / "analysis" / "v203_texture_manifest.json")},
        "photo_reference_manifest": {"path": str((STAGE / "analysis" / "v203_photo_reference_manifest.json").relative_to(ROOT)), "sha256": sha256(STAGE / "analysis" / "v203_photo_reference_manifest.json")},
        "render_manifest": {"path": str((STAGE / "audit" / "v203_render_manifest.json").relative_to(ROOT)), "sha256": sha256(STAGE / "audit" / "v203_render_manifest.json")},
        "occupied_tiles": texture_manifest["occupied_tiles"],
        "photo_references": len(reference_manifest["references"]),
        "renders": len(render_results),
        "protected_hashes": {"V200": EXPECTED_V200_SHA256, "V192": EXPECTED_V192_SHA256},
    }
    write_json(STAGE / "audit" / "v203_build_receipt.json", receipt)
    print(f"V203_BUILD_OK output={OUTPUT.relative_to(ROOT)} sha256={output_hash} textures={len(tile_records) * len(MAP_KINDS)} renders={len(render_results)}")


if __name__ == "__main__":
    main()
