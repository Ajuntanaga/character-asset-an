"""Convert the downloaded CC0 GLB to a native Blend library."""

from pathlib import Path

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "third_party" / "cc0_hands" / "innerscene" / "hand-posable-right.glb"
OUTPUT = ROOT / "third_party" / "cc0_hands" / "innerscene" / "hand-posable-right.blend"


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    for obj in bpy.data.objects:
        obj["source_path"] = str(SOURCE.relative_to(ROOT))
        obj["source_license"] = "CC0"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print(f"V322_CC0_HAND_CONVERTED={OUTPUT}")


if __name__ == "__main__":
    main()
