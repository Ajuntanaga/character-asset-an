"""Reinstall the V257 hand with its evaluated world transform and a true hand mask."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v287_guitar_pose_merge" / "Character_An_guitar_pose_merge_v287.blend"
HAND_SOURCE = ROOT / "production_v257_guitar_surface_contacts" / "Character_An_guitar_surface_contacts_v257.blend"
STAGE = ROOT / "production_v289_explicit_hand_transform"
OUTPUT = STAGE / "Character_An_explicit_hand_transform_v289.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
BODY = "V211_BODY_NEUTRAL"
ASSEMBLY = ("V250_FRETTING_HAND_HUB", "V250_FRETTING_HAND_RIG", "V248_FRETTING_HAND_REALISTIC")
SOURCE_HUB_WORLD = Matrix((
    (0.910937011, -0.368693352, -0.185091615, 0.015254870),
    (-0.137437925, -0.694245458, 0.706494451, -0.975460649),
    (-0.388978869, -0.618133426, -0.683086514, 2.150257826),
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


def mask_native_hand(body):
    names = {group.index: group.name for group in body.vertex_groups}
    mask_group = body.vertex_groups.get("V289_NATIVE_LEFT_HAND") or body.vertex_groups.new(name="V289_NATIVE_LEFT_HAND")
    selected = []
    fragments = ("DEF-hand.L", "DEF-f_", "DEF-thumb", "DEF-palm")
    for vertex in body.data.vertices:
        if any(any(fragment in names.get(item.group, "") for fragment in fragments) and names.get(item.group, "").endswith(".L") and item.weight > .05 for item in vertex.groups):
            selected.append(vertex.index)
    mask_group.add(selected, 1.0, "REPLACE")
    mask = body.modifiers.new("V289_HIDE_NATIVE_LEFT_HAND", "MASK")
    mask.vertex_group = mask_group.name
    mask.invert_vertex_group = True
    return mask, len(selected)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    with bpy.data.libraries.load(str(HAND_SOURCE), link=False) as (source, target):
        target.objects = list(ASSEMBLY)
    loaded = dict(zip(ASSEMBLY, target.objects))
    for obj in loaded.values():
        if not obj.users_collection:
            bpy.context.scene.collection.objects.link(obj)
    hub = loaded["V250_FRETTING_HAND_HUB"]
    hand_rig = loaded["V250_FRETTING_HAND_RIG"]
    hand = loaded["V248_FRETTING_HAND_REALISTIC"]
    hub.parent = None
    hub.matrix_world = SOURCE_HUB_WORLD
    hand_rig.parent = hub
    hand_rig.matrix_parent_inverse = Matrix.Identity(4)
    hand_rig.matrix_basis = Matrix.Identity(4)
    hand.parent = hub
    hand.matrix_parent_inverse = Matrix.Identity(4)
    hand.matrix_basis = Matrix.Identity(4)
    mask, masked_vertices = mask_native_hand(bpy.data.objects[BODY])
    hand["v289_transform_authority"] = "EVALUATED_V257_SOURCE_WORLD_MATRIX"
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "contact_front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0, (1200, 900)),
        "contact_side": (Vector((-0.42, -0.62, 1.42)), Vector((0.26, -0.39, 1.38)), 92.0, (1200, 900)),
    }
    renders = {}
    for label, (location, target_point, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target_point)
        renders[label] = render(scene, camera, RENDERS / f"v289_{label}.png", resolution)
    scene["V289_STATUS"] = "EXPLICIT_V257_HAND_TRANSFORM_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v289-explicit-hand-transform-v1",
        "status": "VISUAL_AND_COLLISION_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hand_source": {"path": str(HAND_SOURCE.relative_to(ROOT)), "sha256": sha(HAND_SOURCE)},
        "hub_world": [[float(value) for value in row] for row in SOURCE_HUB_WORLD],
        "masked_native_vertices": masked_vertices,
        "mask": mask.name,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v289_explicit_hand_transform.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V289_EXPLICIT_HAND_TRANSFORM_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
