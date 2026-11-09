"""Resolve the authoritative v2 visible fingering map into V310 world space."""

from pathlib import Path
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.guitar_geometry import GuitarGeometry, load_authoritative_mapping


NEUTRAL_FRET_X = 0.260
CONTACT_Z = 0.02045
STRING_TOP_Z = 0.02230


def local_pad(geometry, string_id, fret, z=CONTACT_Z):
    point = geometry.local_pad_from_neutral(string_id, fret, behind_fraction=0.18)
    return Vector((NEUTRAL_FRET_X + point[0], point[1], z))


def world_point(root, geometry, string_id, fret, z=CONTACT_Z):
    return root.matrix_world @ local_pad(geometry, string_id, fret, z)


def vec(value):
    return [round(float(item), 7) for item in value]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    geometry = GuitarGeometry.from_mapping(load_authoritative_mapping())
    legacy = {
        "index": ("S5", 9, Vector((0.2671270, -0.4045161, 1.3946022))),
        "middle": ("S4", 10, Vector((0.2444796, -0.4026991, 1.3896780))),
        "ring": ("S7", 9, Vector((0.2757289, -0.4060766, 1.3818460))),
        "pinky": ("S8", 11, Vector((0.2460079, -0.4042325, 1.3534319))),
    }
    visible = {
        "index": ("S6", 11, True),
        "middle": ("S6", 10, False),
        "ring": ("S7", 9, True),
        "pinky": ("S8", 11, True),
    }
    record = {
        "root_matrix_world": [[round(float(value), 9) for value in row] for row in root.matrix_world],
        "legacy_validation": {},
        "visible_pose": {},
    }
    for digit, (string_id, fret, expected) in legacy.items():
        computed = world_point(root, geometry, string_id, fret)
        record["legacy_validation"][digit] = {
            "string": string_id,
            "fret": fret,
            "computed_world_m": vec(computed),
            "legacy_world_m": vec(expected),
            "difference_mm": round((computed - expected).length * 1000.0, 4),
        }
    for digit, (string_id, fret, contact) in visible.items():
        computed = world_point(root, geometry, string_id, fret)
        record["visible_pose"][digit] = {
            "string": string_id,
            "fret": fret,
            "contact": contact,
            "local_pad_m": vec(local_pad(geometry, string_id, fret)),
            "world_pad_m": vec(computed),
        }
    # The local +Z axis is the playing-surface normal. A hovering middle finger
    # stays above its S6/F10 pad rather than depressing the string.
    surface_normal = root.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
    surface_normal.normalize()
    middle_contact = Vector(record["visible_pose"]["middle"]["world_pad_m"])
    record["surface_normal_world"] = vec(surface_normal)
    record["visible_pose"]["middle"]["world_hover_m"] = vec(middle_contact + surface_normal * 0.010)
    print("V315_VISIBLE_TARGETS=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
