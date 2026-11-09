from pathlib import Path

import bpy


package = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/third_party/keentools/packages/keentools-2026_3_1-for-blender.zip")
if not package.is_file():
    raise FileNotFoundError(package)

print("KEENTOOLS_ADDON_INSTALL", bpy.ops.preferences.addon_install(filepath=str(package), overwrite=True))
print("KEENTOOLS_ADDON_ENABLE", bpy.ops.preferences.addon_enable(module="keentools"))
print("KEENTOOLS_ENABLED", "keentools" in bpy.context.preferences.addons)
bpy.ops.wm.save_userpref()
