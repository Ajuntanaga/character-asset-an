"""Fit validated skin pads to the actual string/neck surfaces, not proxy centers."""

from pathlib import Path
from mathutils import Vector
import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE_SCRIPT = ROOT / "pipeline" / "build_v253_surface_contact_fretting.py"
namespace = {"__name__": "v253_surface_solver_library"}
exec(compile(SOURCE_SCRIPT.read_text(encoding="utf-8"), str(SOURCE_SCRIPT), "exec"), namespace)

namespace["STAGE"] = ROOT / "production_v257_guitar_surface_contacts"
namespace["OUTPUT"] = namespace["STAGE"] / "Character_An_guitar_surface_contacts_v257.blend"
namespace["RENDERS"] = namespace["STAGE"] / "renders"
namespace["AUDIT"] = namespace["STAGE"] / "audit"

PROXY_LOCAL = {
    "index": (0.3058091, 0.0041983, "S5", 9, 234),
    "middle": (0.3296208, -0.0042574, "S4", 10, 211),
    "ring": (0.3050833, 0.0209915, "S7", 9, 14),
    "pinky": (0.3488616, 0.0301914, "S8", 11, 225),
}


def string_z_at_x(obj, x: float) -> float:
    points = [Vector(point.co[:3]) for spline in obj.data.splines for point in spline.points]
    for a, b in zip(points, points[1:]):
        if min(a.x, b.x) <= x <= max(a.x, b.x):
            t = (x - a.x) / (b.x - a.x)
            return a.z + t * (b.z - a.z)
    return min(points, key=lambda point: abs(point.x - x)).z


def configure_targets() -> None:
    neck = bpy.data.objects["V206_NECK"]
    contacts = {}
    for digit, (x, y, string, fret, vertex) in PROXY_LOCAL.items():
        string_obj = bpy.data.objects[f"V206_STRING_{string}"]
        radius = float(string_obj.data.bevel_depth)
        # Vertex is the exposed fingertip pad: place it on the top of the
        # depressed string, not at the old proxy-sphere center.
        local_z = string_z_at_x(string_obj, x) - 0.00185 + radius
        world = neck.matrix_world @ Vector((x, y, local_z))
        contacts[digit] = (vertex, world, string, fret)
    namespace["CONTACTS"] = contacts
    # Thumb pad surface sits on the neck back; the old proxy center was 43 mm
    # behind this actual surface.
    namespace["THUMB"] = (286, neck.matrix_world @ Vector((0.3425739, 0.0034927, -0.0270)))


if __name__ == "__main__":
    configure_targets()
    namespace["main"]()
