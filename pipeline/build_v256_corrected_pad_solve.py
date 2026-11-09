"""Run the surface-contact solver with weight-validated V255 pad landmarks."""

from pathlib import Path
import sys
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE_SCRIPT = ROOT / "pipeline" / "build_v253_surface_contact_fretting.py"

# Load the proven evaluated-surface solver as a library, then replace only the
# stage and landmark data. Keeping this experiment isolated preserves V253.
namespace = {"__name__": "v253_surface_solver_library"}
exec(compile(SOURCE_SCRIPT.read_text(encoding="utf-8"), str(SOURCE_SCRIPT), "exec"), namespace)
namespace["STAGE"] = ROOT / "production_v256_corrected_pad_solve"
namespace["OUTPUT"] = namespace["STAGE"] / "Character_An_corrected_pad_solve_v256.blend"
namespace["RENDERS"] = namespace["STAGE"] / "renders"
namespace["AUDIT"] = namespace["STAGE"] / "audit"
namespace["CONTACTS"] = {
    "index": (234, Vector((0.2671270, -0.4045161, 1.3946022)), "S5", 9),
    "middle": (211, Vector((0.2444796, -0.4026991, 1.3896780)), "S4", 10),
    "ring": (14, Vector((0.2757289, -0.4060766, 1.3818460)), "S7", 9),
    "pinky": (225, Vector((0.2460079, -0.4042325, 1.3534319)), "S8", 11),
}
namespace["THUMB"] = (286, Vector((0.247, -0.315, 1.372)))

if __name__ == "__main__":
    namespace["main"]()
