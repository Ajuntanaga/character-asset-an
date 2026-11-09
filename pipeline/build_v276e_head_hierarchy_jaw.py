"""Append the official animation head with intact eye hierarchy and jaw."""

from pathlib import Path
import hashlib, json
import bpy
from mathutils import Matrix, Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v270_boot_finish_cuffs" / "Character_An_boot_finish_cuffs_v270.blend"
LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
STAGE = ROOT / "production_v276e_head_hierarchy_jaw"
OUTPUT = STAGE / "Character_An_head_hierarchy_jaw_v276e.blend"
RENDERS, AUDIT = STAGE / "renders", STAGE / "audit"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def bounds(objects):
    pts = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    return (
        Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
        Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))),
    )


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V270 first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(LIBRARY), link=False) as (src, dst):
        dst.collections = ["Head (Animation) - Realistic"]
        dst.objects = [name for name in ("Jaw - Realistic", "realistic_jaw") if name in src.objects]
    collection = dst.collections[0]
    bpy.context.scene.collection.children.link(collection)
    for obj in dst.objects:
        if obj is not None and not obj.users_collection:
            bpy.context.scene.collection.objects.link(obj)
    appended = [obj for obj in bpy.data.objects if obj not in before]
    head = next(obj for obj in appended if obj.name == "GEO-head_animation_realistic")
    target = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
    source_low, source_high = bounds([head])
    target_low, target_high = bounds([target])
    source_center, target_center = (source_low + source_high) * 0.5, (target_low + target_high) * 0.5
    scale = (target_high.z - target_low.z) / (source_high.z - source_low.z)
    transfer = Matrix.Translation(target_center) @ Matrix.Scale(scale, 4) @ Matrix.Translation(-source_center)

    # Transform only hierarchy roots. Child sclera/iris transforms remain local
    # to their authored parents and therefore receive the alignment exactly once.
    roots = [obj for obj in appended if obj.parent is None]
    for obj in roots:
        obj.matrix_world = transfer @ obj.matrix_world
    for obj in appended:
        obj.name = f"V276E_{obj.name}"

    skin = material("V276E_SKIN_CLAY", (0.36, 0.17, 0.085), 0.56)
    sclera = material("V276E_SCLERA", (0.75, 0.72, 0.65), 0.28)
    iris = material("V276E_IRIS", (0.05, 0.16, 0.12), 0.32)
    jaw_mat = material("V276E_JAW", (0.48, 0.45, 0.40), 0.6)
    for obj in appended:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        lower = obj.name.lower()
        obj.data.materials.append(iris if "iris" in lower else sclera if "sclera" in lower else jaw_mat if "jaw" in lower else skin)

    visible = set(appended)
    for obj in bpy.context.scene.objects:
        obj.hide_render = obj not in visible
    target.hide_render = True

    cam_data = bpy.data.cameras.new("V276E_CAMERA_DATA")
    cam = bpy.data.objects.new("V276E_CAMERA", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = 92
    cam.hide_render = False
    lights = []
    for name, location, energy, size in (
        ("KEY", (-1.2, -1.8, 2.5), 650, 1.8),
        ("FILL", (1.0, -1.4, 1.9), 280, 1.5),
    ):
        data = bpy.data.lights.new(f"V276E_{name}_DATA", "AREA")
        data.energy, data.size = energy, size
        light = bpy.data.objects.new(f"V276E_{name}", data)
        bpy.context.scene.collection.objects.link(light)
        light.location = location
        point_at(light, target_center)
        light.hide_render = False
        lights.append(light)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 768, 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.01, 0.01, 0.01)
    views = {
        "front": Vector((0.0, -2.05, target_center.z)),
        "three_quarter": Vector((-1.15, -1.72, target_center.z + 0.02)),
        "profile": Vector((-2.05, 0.0, target_center.z)),
    }
    renders = []
    for label, location in views.items():
        cam.location = location
        point_at(cam, target_center)
        scene.camera = cam
        path = RENDERS / f"v276e_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders.append(str(path.relative_to(ROOT)))

    records = []
    for obj in appended:
        record = {
            "object": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "world_center": [round(value, 6) for value in obj.matrix_world.translation],
        }
        if obj.type == "MESH":
            record.update(vertices=len(obj.data.vertices), polygons=len(obj.data.polygons), uv_layers=[layer.name for layer in obj.data.uv_layers])
        records.append(record)
    scene["V276E_STATUS"] = "HEAD_HIERARCHY_AND_JAW_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    audit = {
        "schema": "v276e-head-hierarchy-jaw-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "library": {"path": str(LIBRARY.relative_to(ROOT)), "sha256": sha(LIBRARY)},
        "scale": scale,
        "objects": records,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    audit["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276e_head_hierarchy_jaw.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V276E_HEAD_HIERARCHY_OK=" + json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
