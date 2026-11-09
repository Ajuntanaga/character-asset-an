"""Replace the tearing integrated left hand with the bundled realistic hand topology."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v245_arm_performance_pose" / "Character_An_arm_performance_v245.blend"
HAND_LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
STAGE = ROOT / "production_v248_topology_hand_replacement"
OUTPUT = STAGE / "Character_An_topology_hand_v248.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG_NAME = "V239_CLEAN_CHARACTER_RIG"
BODY_NAME = "V211_BODY_NEUTRAL"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def append_hand() -> bpy.types.Object:
    with bpy.data.libraries.load(str(HAND_LIBRARY), link=False) as (_source, target):
        target.objects = ["Hand  - Realistic"]
    hand = target.objects[0]
    bpy.context.scene.collection.objects.link(hand)
    hand.name = "V248_FRETTING_HAND_REALISTIC"
    return hand


def align_hand(hand: bpy.types.Object) -> None:
    # The source hand points down -Z with the thumb along +X.  Match those axes
    # to the V239 left-hand rest pose: fingers down/slightly outward and thumb
    # toward camera.  The anisotropic scale matches the character's hand span.
    z_axis = Vector((-0.43, 0.10, 0.897)).normalized()
    x_hint = Vector((0.0, -1.0, 0.0))
    x_axis = (x_hint - z_axis * x_hint.dot(z_axis)).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    basis = Matrix((x_axis, y_axis, z_axis)).transposed()
    scale = Matrix.Diagonal((0.60, 0.60, 0.74, 1.0))
    rotation = basis.to_4x4()
    transform = rotation @ scale
    source_wrist = Vector((0.0185, 0.0015, 0.0730))
    target_wrist = Vector((0.352, 0.0, 1.055))
    transform.translation = target_wrist - (rotation.to_3x3() @ Vector((source_wrist.x * 0.60, source_wrist.y * 0.60, source_wrist.z * 0.74)))
    hand.matrix_world = transform
    activate(hand)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for polygon in hand.data.polygons:
        polygon.use_smooth = True


def hide_integrated_hand(body: bpy.types.Object) -> int:
    group = body.vertex_groups.get("V248_HIDE_INTEGRATED_LEFT_HAND") or body.vertex_groups.new(name="V248_HIDE_INTEGRATED_LEFT_HAND")
    selected = [
        vertex.index
        for vertex in body.data.vertices
        if vertex.co.x > 0.300 and vertex.co.z < 1.165
    ]
    group.add(selected, 1.0, "REPLACE")
    modifier = body.modifiers.get("V248_HIDE_INTEGRATED_LEFT_HAND") or body.modifiers.new("V248_HIDE_INTEGRATED_LEFT_HAND", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = True
    return len(selected)


def remove_legacy_hand_shell_vertices() -> dict[str, int]:
    """Remove A-pose hand vertices accidentally copied into wardrobe shells."""
    removed = {}
    for name in ("V241_FLORAL_SHIRT", "V241_OPEN_JACKET", "V241_TROUSERS"):
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        doomed = [
            vertex
            for vertex in bm.verts
            if abs(vertex.co.x) > 0.285 and vertex.co.z < 1.205
        ]
        removed[name] = len(doomed)
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
    return removed


def bind(hand: bpy.types.Object, rig: bpy.types.Object) -> bpy.types.Modifier:
    activate(hand)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(
        active_object=rig,
        object=rig,
        selected_objects=[hand, rig],
        selected_editable_objects=[hand, rig],
    ):
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    modifier = next((item for item in hand.modifiers if item.type == "ARMATURE"), None)
    if modifier is None:
        raise RuntimeError("Automatic weights did not create the V248 hand armature modifier")
    modifier.name = "V248_HAND_ARMATURE"
    modifier.use_deform_preserve_volume = True
    return modifier


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V245 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG_NAME]
    body = bpy.data.objects[BODY_NAME]
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    hand = append_hand()
    align_hand(hand)
    modifier = bind(hand, rig)
    hidden_vertices = hide_integrated_hand(body)
    removed_shell_vertices = remove_legacy_hand_shell_vertices()

    skin = bpy.data.materials.get("V248_BODY_SKIN") or bpy.data.materials.new("V248_BODY_SKIN")
    skin.use_nodes = True
    skin.diffuse_color = (0.32, 0.105, 0.045, 1.0)
    bsdf = skin.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.32, 0.105, 0.045, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.48
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.055
    hand.data.materials.clear()
    hand.data.materials.append(skin)

    rig.data.pose_position = "POSE"
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "full_front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 1.00)), 66.0, (900, 1000)),
        "hand_front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0, (1200, 900)),
        "hand_oblique": (Vector((0.86, -1.08, 1.25)), Vector((0.27, -0.39, 1.39)), 95.0, (1200, 900)),
    }
    render_records = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v248_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V248_STATUS"] = "REALISTIC_HAND_TOPOLOGY_BOUND_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v248-topology-hand-replacement-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "hand_library": {"path": str(HAND_LIBRARY.relative_to(ROOT)), "sha256": sha256(HAND_LIBRARY)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "hand": hand.name,
        "vertices": len(hand.data.vertices),
        "polygons": len(hand.data.polygons),
        "vertex_groups": len(hand.vertex_groups),
        "armature_modifier": modifier.name,
        "hidden_integrated_hand_vertices": hidden_vertices,
        "removed_legacy_hand_shell_vertices": removed_shell_vertices,
        "renders": render_records,
    }
    (AUDIT / "v248_topology_hand.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V248_TOPOLOGY_HAND_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
