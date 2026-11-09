"""Refit the wrist from V258 residuals, then rerun collision-aware fingers."""

from pathlib import Path
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SCRIPT = ROOT / "pipeline" / "build_v258_collision_aware_fretting.py"
module = {"__name__": "v258_collision_library"}
exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), module)
module["configure"]()
solver = module["ns"]
solver["STAGE"] = ROOT / "production_v259_collision_wrist_refit"
solver["OUTPUT"] = solver["STAGE"] / "Character_An_collision_wrist_refit_v259.blend"
solver["RENDERS"] = solver["STAGE"] / "renders"
solver["AUDIT"] = solver["STAGE"] / "audit"
# Mean V258 pad residual, applied to the global wrist before local articulation.
solver["WRIST_DELTA"] = Vector((-0.0801659, 0.0634162, -0.0250174))

if __name__ == "__main__":
    solver["main"]()
