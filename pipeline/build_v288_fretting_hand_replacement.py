"""Install the intact V257/V250 fretting-hand assembly into the V287 character."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v287_guitar_pose_merge" / "Character_An_guitar_pose_merge_v287.blend"
HAND_SOURCE = ROOT / "production_v257_guitar_surface_contacts" / "Character_An_guitar_surface_contacts_v257.blend"
STAGE = ROOT / "production_v288_fretting_hand_replacement"
OUTPUT = STAGE / "Character_An_fretting_hand_replacement_v288.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
BODY = "V211_BODY_NEUTRAL"
ASSEMBLY = ("V250_FRETTING_HAND_HUB", "V250_FRETTING_HAND_RIG", "V248_FRETTING_HAND_REALISTIC")


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


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    with bpy.data.libraries.load(str(HAND_SOURCE), link=False) as (source, target):
        missing = [name for name in ASSEMBLY if name not in source.objects]
        if missing:
            raise RuntimeError(f"Missing hand assembly: {missing}")
        target.objects = list(ASSEMBLY)
    loaded = dict(zip(ASSEMBLY, target.objects))
    for obj in loaded.values():
        if not obj.users_collection:
            bpy.context.scene.collection.objects.link(obj)
    hub = loaded["V250_FRETTING_HAND_HUB"]
    hand_rig = loaded["V250_FRETTING_HAND_RIG"]
    hand = loaded["V248_FRETTING_HAND_REALISTIC"]
    main_rig = bpy.data.objects[MAIN_RIG]
    hub_world = hub.matrix_world.copy()
    hub.parent = main_rig
    hub.parent_type = "BONE"
    hub.parent_bone = "DEF-hand.L"
    hub.matrix_world = hub_world
    if hand_rig.parent != hub:
        world = hand_rig.matrix_world.copy(); hand_rig.parent = hub; hand_rig.matrix_world = world
    if hand.parent != hub:
        world = hand.matrix_world.copy(); hand.parent = hub; hand.matrix_world = world
    body = bpy.data.objects[BODY]
    mask = body.modifiers.get("V288_HIDE_NATIVE_LEFT_HAND") or body.modifiers.new("V288_HIDE_NATIVE_LEFT_HAND", "MASK")
    mask.vertex_group = "DEF-hand.L"
    mask.invert_vertex_group = True
    hand["v288_contact_authority"] = "V257_SURFACE_TARGETS_V250_INTACT_ARCHITECTURE"
    hand["v288_acceptance"] = "VISUAL_AND_COLLISION_REVIEW_REQUIRED"
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
        renders[label] = render(scene, camera, RENDERS / f"v288_{label}.png", resolution)
    scene["V288_STATUS"] = "FRETTING_HAND_INSTALLED_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v288-fretting-hand-replacement-v1",
        "status": "INSTALLED_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hand_source": {"path": str(HAND_SOURCE.relative_to(ROOT)), "sha256": sha(HAND_SOURCE)},
        "assembly": list(ASSEMBLY),
        "native_left_hand_hidden_by": mask.name,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v288_fretting_hand_replacement.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V288_FRETTING_HAND_REPLACEMENT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
