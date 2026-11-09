"""Mirror the intact V250 dedicated hand onto the right wrist for picking."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v289_explicit_hand_transform" / "Character_An_explicit_hand_transform_v289.blend"
HAND_SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
STAGE = ROOT / "production_v292_dedicated_picking_hand"
OUTPUT = STAGE / "Character_An_dedicated_picking_hand_v292.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
BODY = "V211_BODY_NEUTRAL"
SOURCE_LEFT_HAND_WORLD = Matrix((
    (-0.599999905, 0.742781162, -0.297112197, 0.194999829),
    (-0.799999774, -0.557085693, 0.222834542, -0.345002770),
    (0.000000325, 0.371390522, 0.928476691, 1.339999080),
    (0.0, 0.0, 0.0, 1.0),
))
SOURCE_HUB_WORLD = Matrix((
    (0.910937011, -0.368693352, -0.185091615, 0.069621518),
    (-0.137437925, -0.694245458, 0.706494451, -1.041975856),
    (-0.388978869, -0.618133426, -0.683086514, 2.197576046),
    (0.0, 0.0, 0.0, 1.0),
))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, resolution):
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def mask_native_right_hand(body):
    names = {group.index: group.name for group in body.vertex_groups}
    group = body.vertex_groups.new(name="V292_NATIVE_RIGHT_HAND")
    selected = []
    fragments = ("DEF-hand.R", "DEF-f_", "DEF-thumb", "DEF-palm")
    for vertex in body.data.vertices:
        if any(any(fragment in names.get(item.group, "") for fragment in fragments) and names.get(item.group, "").endswith(".R") and item.weight > .05 for item in vertex.groups):
            selected.append(vertex.index)
    group.add(selected, 1.0, "REPLACE")
    modifier = body.modifiers.new("V292_HIDE_NATIVE_RIGHT_HAND", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = True
    return modifier, len(selected)


def create_pick(center, rig):
    vertices = [
        center + Vector((-0.009, -0.002, 0.006)),
        center + Vector((0.009, -0.002, 0.006)),
        center + Vector((0.0, -0.002, -0.013)),
    ]
    mesh = bpy.data.meshes.new("V292_PLECTRUM_MESH")
    mesh.from_pydata(vertices, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new("V292_PLECTRUM", mesh)
    bpy.context.scene.collection.objects.link(obj)
    material = bpy.data.materials.new("V292_PLECTRUM_PURPLE")
    material.diffuse_color = (.04, .01, .09, 1.0)
    mesh.materials.append(material)
    solid = obj.modifiers.new("V292_PICK_THICKNESS", "SOLIDIFY")
    solid.thickness = .0008
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "index_03"
    obj.matrix_world = world
    return obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    main_rig = bpy.data.objects[MAIN_RIG]
    right_hand_world = main_rig.matrix_world @ main_rig.pose.bones["DEF-hand.R"].matrix
    mirror = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
    delta = right_hand_world @ (mirror @ SOURCE_LEFT_HAND_WORLD).inverted()
    target_hub_world = delta @ mirror @ SOURCE_HUB_WORLD

    source_names = ("V250_FRETTING_HAND_HUB", "V250_FRETTING_HAND_RIG", "V248_FRETTING_HAND_REALISTIC")
    with bpy.data.libraries.load(str(HAND_SOURCE), link=False) as (source, target):
        target.objects = list(source_names)
    hub, hand_rig, hand = target.objects
    for obj in (hub, hand_rig, hand):
        if not obj.users_collection:
            bpy.context.scene.collection.objects.link(obj)
    hub.name = "V292_PICKING_HAND_HUB"
    hand_rig.name = "V292_PICKING_HAND_RIG"
    hand.name = "V292_PICKING_HAND_REALISTIC"
    hub.parent = None
    hub.matrix_world = target_hub_world
    hand_rig.parent = hub
    hand_rig.matrix_parent_inverse = Matrix.Identity(4)
    hand_rig.matrix_basis = Matrix.Identity(4)
    hand.parent = hub
    hand.matrix_parent_inverse = Matrix.Identity(4)
    hand.matrix_basis = Matrix.Identity(4)
    hub_world = hub.matrix_world.copy()
    hub.parent = main_rig
    hub.parent_type = "BONE"
    hub.parent_bone = "DEF-hand.R"
    hub.matrix_world = hub_world
    mask, masked_vertices = mask_native_right_hand(bpy.data.objects[BODY])

    flex = {
        "index": (0.10, 0.65, 0.40),
        "middle": (0.25, 0.85, 0.55),
        "ring": (0.30, 0.90, 0.60),
        "pinky": (0.35, 0.95, 0.65),
        "thumb": (0.15, 0.50, 0.35),
    }
    for digit, angles in flex.items():
        for joint, angle in enumerate(angles, start=1):
            bone = hand_rig.pose.bones[f"{digit}_{joint:02d}"]
            bone.rotation_mode = "XYZ"
            bone.rotation_euler.x = angle
    bpy.context.view_layer.update()
    index_tip = hand_rig.matrix_world @ hand_rig.pose.bones["index_03"].tail
    thumb_tip = hand_rig.matrix_world @ hand_rig.pose.bones["thumb_03"].tail
    pick = create_pick(index_tip.lerp(thumb_tip, .5), hand_rig)

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "picking_macro": (Vector((-1.22, -1.66, 1.28)), Vector((-0.10, -0.35, 1.23)), 100.0, (1200, 900)),
        "three_quarter": (Vector((-2.55, -2.75, 1.14)), Vector((0.0, -0.03, 1.02)), 70.0, (900, 1000)),
    }
    renders = {}
    for label, (location, target_point, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target_point)
        renders[label] = render(scene, camera, RENDERS / f"v292_{label}.png", resolution)
    scene["V292_STATUS"] = "DEDICATED_PICKING_HAND_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v292-dedicated-picking-hand-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hand_source": {"path": str(HAND_SOURCE.relative_to(ROOT)), "sha256": sha(HAND_SOURCE)},
        "masked_native_vertices": masked_vertices,
        "mask": mask.name,
        "flex_xyz_x_rad": flex,
        "pick": pick.name,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v292_dedicated_picking_hand.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V292_DEDICATED_PICKING_HAND_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
