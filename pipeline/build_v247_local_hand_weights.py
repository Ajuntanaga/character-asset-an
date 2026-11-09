"""Repair only the fretting-hand skin weights against corrected rest bones."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v246_exact_fretting_solve" / "Character_An_exact_fretting_v246.blend"
STAGE = ROOT / "production_v247_local_hand_weights"
OUTPUT = STAGE / "Character_An_local_hand_weights_v247.blend"
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


def segment_distance(point: Vector, start: Vector, end: Vector) -> float:
    vector = end - start
    length_squared = vector.length_squared
    if length_squared <= 1e-12:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(vector) / length_squared))
    return (point - (start + factor * vector)).length


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V246 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG_NAME]
    body = bpy.data.objects[BODY_NAME]
    hand_bones = ["DEF-forearm.L", "DEF-hand.L"]
    hand_bones += [f"DEF-palm.0{number}.L" for number in range(1, 5)]
    for digit in ("index", "middle", "ring", "pinky"):
        hand_bones += [f"DEF-f_{digit}.0{joint}.L" for joint in range(1, 4)]
    hand_bones += [f"DEF-thumb.0{joint}.L" for joint in range(1, 4)]
    missing = [name for name in hand_bones if name not in rig.data.bones]
    if missing:
        raise RuntimeError(f"Missing deform bones: {missing}")

    segments = {
        name: (
            rig.matrix_world @ rig.data.bones[name].head_local,
            rig.matrix_world @ rig.data.bones[name].tail_local,
        )
        for name in hand_bones
    }
    hand_only = [name for name in hand_bones if name != "DEF-forearm.L"]
    candidates = []
    distances_by_vertex = {}
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        if not (point.x > 0.275 and 0.94 < point.z < 1.230 and abs(point.y) < 0.145):
            continue
        distances = {
            name: segment_distance(point, *segments[name])
            for name in hand_bones
        }
        if min(distances[name] for name in hand_only) <= 0.145:
            candidates.append(vertex.index)
            distances_by_vertex[vertex.index] = distances
    if len(candidates) < 200:
        raise RuntimeError(f"Hand envelope too small: {len(candidates)} vertices")

    deform_groups = [
        group for group in body.vertex_groups
        if group.name.startswith("DEF-")
    ]
    for group in deform_groups:
        group.remove(candidates)
    groups = {
        name: body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
        for name in hand_bones
    }
    influence_counts = {name: 0 for name in hand_bones}
    for index in candidates:
        ranked = sorted(distances_by_vertex[index].items(), key=lambda item: item[1])
        minimum = ranked[0][1]
        selected = [item for item in ranked[:4] if item[1] <= minimum + 0.020]
        raw = [(name, 1.0 / ((distance + 0.0025) ** 3.0)) for name, distance in selected]
        total = sum(value for _, value in raw)
        for name, value in raw:
            weight = value / total
            groups[name].add([index], weight, "REPLACE")
            if weight >= 0.20:
                influence_counts[name] += 1
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "full_front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 1.00)), 66.0, (900, 1000)),
        "hand_front": (Vector((0.64, -1.36, 1.45)), Vector((0.27, -0.40, 1.39)), 110.0, (1200, 900)),
        "hand_oblique": (Vector((0.86, -1.02, 1.30)), Vector((0.27, -0.40, 1.39)), 100.0, (1200, 900)),
    }
    render_records = {}
    for label, (location, target_point, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target_point)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v247_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V247_STATUS"] = "LOCAL_FRETTING_HAND_NEAREST_SEGMENT_WEIGHTS"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v247-local-hand-weights-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "candidate_vertices": len(candidates),
        "hand_bones": hand_bones,
        "influence_counts_ge_020": influence_counts,
        "preserved_outside_envelope": True,
        "renders": render_records,
    }
    (AUDIT / "v247_hand_weight_audit.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V247_LOCAL_HAND_WEIGHTS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
