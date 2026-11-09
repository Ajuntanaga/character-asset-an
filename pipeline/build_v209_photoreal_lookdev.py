from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v209_lookdev"
SOURCE = ROOT / "production_v208_rig" / "ant_performance_rig_v208.blend"
OUTPUT = STAGE / "ant_photoreal_lookdev_v209.blend"
EXPECTED_SOURCE_SHA256 = "1e9e356fa897a46bae906c9d203a06db53ffebeece36d3935a623d5212f93c73"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def collection(name: str) -> bpy.types.Collection:
    value = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if value.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(value)
    return value


def principled_base(name: str) -> tuple[bpy.types.Material, bpy.types.Node, bpy.types.NodeTree]:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    return mat, surface, mat.node_tree


def skin_material() -> bpy.types.Material:
    mat, surface, tree = principled_base("MAT_V209_SKIN_PHOTOREAL")
    nodes, links = tree.nodes, tree.links
    surface.inputs["Roughness"].default_value = 0.58
    surface.inputs["IOR"].default_value = 1.40
    surface.inputs["Subsurface Weight"].default_value = 0.060
    surface.inputs["Subsurface Radius"].default_value = (1.0, 0.36, 0.18)
    texcoord = nodes.new("ShaderNodeTexCoord")
    color_noise = nodes.new("ShaderNodeTexNoise")
    color_noise.inputs["Scale"].default_value = 5.2
    color_noise.inputs["Detail"].default_value = 4.0
    color_noise.inputs["Roughness"].default_value = 0.63
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.018, 0.0038, 0.0015, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.145, 0.032, 0.012, 1.0)
    pore = nodes.new("ShaderNodeTexNoise")
    pore.inputs["Scale"].default_value = 115.0
    pore.inputs["Detail"].default_value = 7.0
    pore.inputs["Roughness"].default_value = 0.76
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.00018
    links.new(texcoord.outputs["Object"], color_noise.inputs["Vector"])
    links.new(color_noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    links.new(texcoord.outputs["Object"], pore.inputs["Vector"])
    links.new(pore.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], surface.inputs["Normal"])
    mat.diffuse_color = (0.115, 0.026, 0.010, 1.0)
    mat["v209_pbr"] = True
    return mat


def fabric_material(name: str, base: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    mat, surface, tree = principled_base(name)
    nodes, links = tree.nodes, tree.links
    surface.inputs["Base Color"].default_value = base
    surface.inputs["Roughness"].default_value = roughness
    texcoord = nodes.new("ShaderNodeTexCoord")
    wave_a = nodes.new("ShaderNodeTexWave")
    wave_a.wave_type = "BANDS"
    wave_a.bands_direction = "X"
    wave_a.inputs["Scale"].default_value = 185.0
    wave_a.inputs["Distortion"].default_value = 3.0
    wave_b = nodes.new("ShaderNodeTexWave")
    wave_b.wave_type = "BANDS"
    wave_b.bands_direction = "Y"
    wave_b.inputs["Scale"].default_value = 210.0
    mix = nodes.new("ShaderNodeMath")
    mix.operation = "MULTIPLY"
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.19
    bump.inputs["Distance"].default_value = 0.00025
    links.new(texcoord.outputs["Generated"], wave_a.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], wave_b.inputs["Vector"])
    links.new(wave_a.outputs["Color"], mix.inputs[0])
    links.new(wave_b.outputs["Color"], mix.inputs[1])
    links.new(mix.outputs["Value"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], surface.inputs["Normal"])
    mat.diffuse_color = base
    mat["v209_pbr"] = True
    return mat


def leather_material() -> bpy.types.Material:
    mat, surface, tree = principled_base("MAT_V209_BOOT_LEATHER")
    nodes, links = tree.nodes, tree.links
    surface.inputs["Roughness"].default_value = 0.42
    surface.inputs["Coat Weight"].default_value = 0.09
    surface.inputs["Coat Roughness"].default_value = 0.28
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 34.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.70
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.012, 0.0025, 0.0012, 1.0)
    ramp.color_ramp.elements[1].color = (0.105, 0.020, 0.006, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.20
    bump.inputs["Distance"].default_value = 0.00035
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], surface.inputs["Normal"])
    mat.diffuse_color = (0.070, 0.012, 0.004, 1.0)
    mat["v209_pbr"] = True
    return mat


def rubber_material() -> bpy.types.Material:
    mat, surface, _tree = principled_base("MAT_V209_SOLE_RUBBER")
    surface.inputs["Base Color"].default_value = (0.003, 0.004, 0.005, 1.0)
    surface.inputs["Roughness"].default_value = 0.72
    mat.diffuse_color = (0.003, 0.004, 0.005, 1.0)
    mat["v209_pbr"] = True
    return mat


def replace_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def merge_surface(name: str, objects: list[bpy.types.Object], mat: bpy.types.Material, voxel_size: float, target: bpy.types.Collection) -> bpy.types.Object:
    require(objects, f"No objects for {name}")
    duplicates = []
    for source in objects:
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.animation_data_clear()
        duplicate.parent = None
        duplicate.matrix_world = source.matrix_world.copy()
        target.objects.link(duplicate)
        duplicates.append(duplicate)
        source.hide_render = True
    bpy.ops.object.select_all(action="DESELECT")
    for duplicate in duplicates:
        duplicate.select_set(True)
    bpy.context.view_layer.objects.active = duplicates[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.name = name
    replace_material(joined, mat)
    remesh = joined.modifiers.new("V209 continuous voxel union", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = voxel_size
    remesh.use_smooth_shade = True
    bpy.context.view_layer.objects.active = joined
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth = joined.modifiers.new("V209 tissue smoothing", "SMOOTH")
    smooth.factor = 0.32
    smooth.iterations = 3
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    joined["v209_continuous_surface"] = True
    joined["source_object_count"] = len(objects)
    joined["voxel_size_m"] = voxel_size
    return joined


def prune_small_islands(obj: bpy.types.Object, minimum_vertices: int) -> int:
    adjacency = [[] for _ in obj.data.vertices]
    for edge in obj.data.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    unseen = set(range(len(adjacency)))
    remove: set[int] = set()
    while unseen:
        seed = unseen.pop()
        component = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        if len(component) < minimum_vertices:
            remove.update(component)
    if not remove:
        return 0
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for index in remove:
        obj.data.vertices[index].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj["pruned_island_vertices"] = len(remove)
    return len(remove)


def add_camera(name: str, location: tuple[float, float, float], look: tuple[float, float, float], lens: float, target: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.cameras.new(name + "_DATA")
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(look) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def add_light(name: str, location: tuple[float, float, float], look: tuple[float, float, float], energy: float, size: float, target: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.lights.new(name + "_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(look) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def build() -> dict[str, object]:
    target = collection("V209_PHOTOREAL_LOOKDEV")
    for obj in tuple(target.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    skin = skin_material()
    jacket = fabric_material("MAT_V209_CHARCOAL_FABRIC", (0.015, 0.018, 0.022, 1.0), 0.78)
    trouser = fabric_material("MAT_V209_TROUSER_FABRIC", (0.004, 0.005, 0.006, 1.0), 0.74)
    leather = leather_material()
    rubber = rubber_material()

    replace_material(bpy.data.objects["V208_BODY_WITHOUT_NEUTRAL_ARMS"], skin)
    replace_material(bpy.data.objects["V208_JACKET_TORSO"], jacket)
    replace_material(bpy.data.objects["V205_FITTED_TROUSERS_SHELL"], trouser)
    for obj in bpy.data.objects:
        if obj.name.startswith(("V205_FITTED_BOOT_", "V205_BOOT_")) and obj.type == "MESH":
            replace_material(obj, leather)
        if "SOLE" in obj.name and obj.type == "MESH":
            replace_material(obj, rubber)
        if obj.name.startswith("V207_") and "_CREASE_" in obj.name:
            obj.hide_render = True

    bpy.ops.mesh.primitive_torus_add(major_radius=0.105, minor_radius=0.014, major_segments=64, minor_segments=16, location=(0.0, -0.004, 1.485))
    collar = bpy.context.object
    collar.name = "V209_TAILORED_NECKLINE"
    collar.scale.y = 0.76
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for owner in tuple(collar.users_collection):
        owner.objects.unlink(collar)
    target.objects.link(collar)
    collar.data.materials.append(jacket)
    collar["role"] = "continuous tailored neckline covering trimmed-shell boundary"

    fretting_sources = [
        obj for obj in bpy.data.objects
        if obj.type == "MESH"
        and obj.name.startswith("V207_")
        and any(token in obj.name for token in ("FRETTING_PALM", "THENAR", "WRIST", "SEGMENT", "DISTAL_BLEND", "CONTACT_PAD", "THUMB_REAR_PAD"))
        and "JACKET_CUFF" not in obj.name
    ]
    picking_sources = [
        obj for obj in bpy.data.objects
        if obj.type == "MESH"
        and obj.name.startswith("V208_PICKING_")
        and "_SLEEVE_" not in obj.name
        and not obj.name.endswith("_CUFF")
    ]
    sleeve_sources = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith("V208_") and ("_SLEEVE_" in obj.name or obj.name.endswith("_CUFF"))]
    fretting = merge_surface("V209_FRETTING_HAND_CONTINUOUS", fretting_sources, skin, 0.0032, target)
    picking = merge_surface("V209_PICKING_HAND_CONTINUOUS", picking_sources, skin, 0.0028, target)
    sleeves = merge_surface("V209_SLEEVES_CONTINUOUS", sleeve_sources, jacket, 0.0060, target)
    prune_small_islands(fretting, 250)

    hair_mat = bpy.data.materials.get("MAT_V204_GROOM")
    if hair_mat and hair_mat.use_nodes:
        bsdf = hair_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.004, 0.003, 0.002, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.58
    for obj in bpy.data.objects:
        if obj.name.startswith("V204_") and obj.type in {"CURVES", "CURVE"}:
            obj.hide_render = False

    scene = bpy.context.scene
    scene["checkpoint"] = "V209_PHOTOREAL_LOOKDEV"
    scene["source_v208_sha256"] = EXPECTED_SOURCE_SHA256
    scene["v209_surface_unions"] = json.dumps({"fretting": fretting.name, "picking": picking.name, "sleeves": sleeves.name}, sort_keys=True)
    return {"fretting": fretting, "picking": picking, "sleeves": sleeves, "materials": [skin, jacket, trouser, leather, rubber]}


def render_suite(cameras: dict[str, bpy.types.Object]) -> dict[str, object]:
    scene = bpy.context.scene
    render_dir = STAGE / "renders" / "hero"
    render_dir.mkdir(parents=True, exist_ok=True)
    visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.hide_render = not obj.name.startswith("V209_")
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 56
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -1.35
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.004, 0.006, 0.010, 1.0)
        background.inputs["Strength"].default_value = 0.075
    manifest = {"renderer": "Cycles CPU 56 spp, denoised", "renders": {}}
    try:
        for label, camera in cameras.items():
            scene.camera = camera
            if label in {"front", "three_quarter", "profile", "hero"}:
                scene.render.resolution_x, scene.render.resolution_y = 768, 1024
            else:
                scene.render.resolution_x, scene.render.resolution_y = 900, 700
            output = render_dir / f"{label}.png"
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
            manifest["renders"][label] = {"path": str(output.relative_to(ROOT)), "sha256": sha256(output)}
    finally:
        for name, hidden in visibility.items():
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_render = hidden
    write_json(STAGE / "audit" / "v209_render_manifest.json", manifest)
    return manifest


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open accepted V208 source first: {SOURCE}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V208 source hash changed")
    STAGE.joinpath("audit").mkdir(parents=True, exist_ok=True)
    result = build()
    target = collection("V209_PHOTOREAL_LOOKDEV")
    cameras = {
        "front": add_camera("V209_CAM_FRONT", (0.0, -4.1, 0.98), (0.0, -0.02, 0.95), 74, target),
        "three_quarter": add_camera("V209_CAM_THREE_QUARTER", (2.5, -3.4, 1.20), (0.0, -0.02, 1.00), 82, target),
        "profile": add_camera("V209_CAM_PROFILE", (-3.5, -0.35, 1.08), (0.0, -0.02, 1.00), 86, target),
        "hero": add_camera("V209_CAM_HERO", (1.75, -3.1, 1.38), (0.0, -0.04, 1.04), 96, target),
        "fretting_macro": add_camera("V209_CAM_FRETTING", (-0.52, -1.10, 1.48), (-0.28, -0.19, 1.20), 120, target),
        "picking_macro": add_camera("V209_CAM_PICKING", (0.48, -1.02, 1.26), (0.04, -0.22, 1.00), 120, target),
    }
    add_light("V209_KEY", (1.2, -2.2, 3.4), (0.0, 0.0, 1.05), 540.0, 1.35, target)
    add_light("V209_FILL", (-2.0, -1.2, 2.2), (0.0, 0.0, 1.05), 135.0, 1.10, target)
    add_light("V209_RIM", (0.4, 1.9, 2.9), (0.0, 0.0, 1.2), 360.0, 0.95, target)
    audit = {
        "schema": "v209-photoreal-lookdev-v1",
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "continuous_surfaces": {key: {"name": result[key].name, "vertices": len(result[key].data.vertices), "voxel_size_m": result[key]["voxel_size_m"]} for key in ("fretting", "picking", "sleeves")},
        "materials": [mat.name for mat in result["materials"]],
    }
    write_json(STAGE / "audit" / "v209_lookdev_audit.json", audit)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    render_suite(cameras)
    output_hash = sha256(OUTPUT)
    write_json(STAGE / "audit" / "v209_build_receipt.json", {
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash},
        "lookdev_audit_sha256": sha256(STAGE / "audit" / "v209_lookdev_audit.json"),
        "render_manifest_sha256": sha256(STAGE / "audit" / "v209_render_manifest.json"),
    })
    print(f"V209_PHOTOREAL_LOOKDEV_OK output_sha256={output_hash} continuous_surfaces=3")


if __name__ == "__main__":
    main()
