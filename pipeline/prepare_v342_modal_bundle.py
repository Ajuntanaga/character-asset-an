"""Create a self-contained V342 blend for remote rendering."""
from pathlib import Path

import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v342_graphite_contour_guitar" / "Character_An_graphite_contour_guitar_v342.blend"
OUTPUT = ROOT / "production_v342_graphite_contour_guitar" / "modal" / "Character_An_v342_packed.blend"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print(f"V342_MODAL_BUNDLE={OUTPUT}")
