"""Finish V269 Chelsea boots and replace rigid trouser cuff rings."""

from pathlib import Path
import hashlib, json, math, bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v269_reference_chelsea_boots" / "Character_An_reference_chelsea_boots_v269.blend"
STAGE = ROOT / "production_v270_boot_finish_cuffs"
OUTPUT = STAGE / "Character_An_boot_finish_cuffs_v270.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def parent_bone(obj, bone):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def tune_leather():
    mat = bpy.data.materials["MAT_V269_BURNISHED_COGNAC"]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    noise = nodes.get("V270_FINE_GRAIN") or nodes.new("ShaderNodeTexNoise")
    noise.name = "V270_FINE_GRAIN"
    noise.inputs["Scale"].default_value = 175.0
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.get("V270_GRAIN_ROUGHNESS") or nodes.new("ShaderNodeValToRGB")
    ramp.name = "V270_GRAIN_ROUGHNESS"
    ramp.color_ramp.elements[0].position = 0.27
    ramp.color_ramp.elements[0].color = (0.20, 0.20, 0.20, 1)
    ramp.color_ramp.elements[1].position = 0.73
    ramp.color_ramp.elements[1].color = (0.48, 0.48, 0.48, 1)
    bump = nodes.get("V270_LEATHER_PORE") or nodes.new("ShaderNodeBump")
    bump.name = "V270_LEATHER_PORE"
    bump.inputs["Strength"].default_value = 0.13
    bump.inputs["Distance"].default_value = 0.00022
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def curve_line(name, points, collection, material, bevel=0.0012):
    curve = bpy.data.curves.new(name + "_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def cloth_cuff(name, cx, collection, material):
    seg = 32
    levels = [(0.276, 0.069, 0.058), (0.283, 0.076, 0.064), (0.316, 0.076, 0.064), (0.324, 0.068, 0.057)]
    verts = []
    for ring_index, (z, rx, ry) in enumerate(levels):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            wrinkle = 1.0 + 0.018 * math.sin(3 * a + ring_index * 0.7) + 0.010 * math.sin(7 * a)
            verts.append((cx + rx * wrinkle * math.cos(a), 0.009 + ry * wrinkle * math.sin(a), z + 0.0015 * math.sin(5 * a)))
    faces = []
    for row in range(len(levels) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((row * seg + i, row * seg + j, (row + 1) * seg + j, (row + 1) * seg + i))
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    bevel = obj.modifiers.new(name + "_SOFT_EDGE", "BEVEL")
    bevel.width = 0.0025
    bevel.segments = 3
    solid = obj.modifiers.new(name + "_THICKNESS", "SOLIDIFY")
    solid.thickness = 0.003
    return obj


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V269 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    tune_leather()

    for side in ("L", "R"):
        old = bpy.data.objects.get(f"V243_ROLLED_CUFF_{side}")
        if old:
            old.hide_render = True
            old.hide_viewport = True

    collection = bpy.data.collections.get("V270_BOOT_FINISH") or bpy.data.collections.new("V270_BOOT_FINISH")
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    stitch_mat = bpy.data.materials.get("MAT_V270_BOOT_STITCH") or bpy.data.materials.new("MAT_V270_BOOT_STITCH")
    stitch_mat.diffuse_color = (0.055, 0.024, 0.009, 1)
    cuff_mat = bpy.data.materials.get("MAT_V264_DEEP_BLACK_TROUSERS") or bpy.data.materials.get("MAT_V243_TROUSER_DETAIL")
    made = []

    for side, cx in (("L", -0.165), ("R", 0.165)):
        cuff = cloth_cuff(f"V270_SHAPED_CUFF_{side}", cx, collection, cuff_mat)
        parent_bone(cuff, f"shin_fk.{side}")
        made.append(cuff)
        # Vamp line and quarter seam are deliberately subtle at character scale.
        vamp = curve_line(
            f"V270_VAMP_SEAM_{side}",
            [(cx - 0.050, -0.012, 0.104), (cx, -0.030, 0.122), (cx + 0.050, -0.012, 0.104)],
            collection, stitch_mat, 0.0010,
        )
        quarter = curve_line(
            f"V270_QUARTER_SEAM_{side}",
            [(cx - 0.050, 0.055, 0.124), (cx, 0.080, 0.143), (cx + 0.050, 0.055, 0.124)],
            collection, stitch_mat, 0.0009,
        )
        for obj in (vamp, quarter):
            parent_bone(obj, f"foot_fk.{side}")
            made.append(obj)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    cam = bpy.data.objects["CAM_V211_FRONT"]
    rig = bpy.data.objects[RIG]
    hand = bpy.data.objects["V250_FRETTING_HAND_RIG"]
    old_rig, old_hand = rig.data.pose_position, hand.data.pose_position
    guitar = [obj for obj in scene.objects if obj.name.startswith("V206_")]
    guitar_state = {obj.name: (obj.hide_render, obj.hide_viewport) for obj in guitar}
    rig.data.pose_position = "REST"
    hand.data.pose_position = "REST"
    for obj in guitar:
        obj.hide_render = True
        obj.hide_viewport = True
    bpy.context.view_layer.update()
    views = {
        "boots_front": (Vector((0, -1.40, 0.23)), Vector((0, -0.03, 0.16)), 92, (1100, 800)),
        "boots_three_quarter": (Vector((-0.64, -1.16, 0.29)), Vector((0, -0.03, 0.16)), 92, (1100, 800)),
        "boots_profile": (Vector((-1.18, -0.02, 0.26)), Vector((0, -0.03, 0.16)), 92, (1100, 800)),
        "neutral_full": (Vector((0, -4.15, 1.03)), Vector((0, 0, 1.03)), 70, (900, 1200)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        cam.location = location
        cam.data.lens = lens
        point_at(cam, target)
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v270_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
    rig.data.pose_position, hand.data.pose_position = old_rig, old_hand
    for obj in guitar:
        obj.hide_render, obj.hide_viewport = guitar_state[obj.name]
    bpy.context.view_layer.update()

    record = {
        "schema": "v270-boot-finish-cuffs-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "objects": [obj.name for obj in made],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V270_STATUS"] = "BOOT_FINISH_CUFFS_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v270_boot_finish_cuffs.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V270_BOOT_FINISH_CUFFS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
