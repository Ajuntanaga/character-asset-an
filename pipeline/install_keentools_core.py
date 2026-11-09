"""Install and verify the downloaded KeenTools Core in the live Blender."""

from pathlib import Path

import bpy

from keentools.blender_independent_packages import pykeentools_loader
from keentools.preferences.progress import InstallationProgress


PACKAGE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "third_party/keentools/packages/keentools-core-2026.3.1-linux.zip"
)
EXPECTED_SIZE = 146_529_549

if not PACKAGE.is_file() or PACKAGE.stat().st_size != EXPECTED_SIZE:
    raise RuntimeError(
        f"Core package is missing or incomplete: {PACKAGE} "
        f"({PACKAGE.stat().st_size if PACKAGE.exists() else 0}/{EXPECTED_SIZE})"
    )

operator_result = bpy.ops.keentools_preferences.install_pkt_from_file(
    "EXEC_DEFAULT", filepath=str(PACKAGE), license_accepted=True
)
state = InstallationProgress.get_state()
installed, status = pykeentools_loader.installation_status(force_recheck=True)
if "FINISHED" not in operator_result or state["active"] or not installed:
    raise RuntimeError(
        f"Core installation failed: operator={operator_result}, progress={state}, status={status}"
    )

module = pykeentools_loader.module()
version = module.version
bpy.context.scene["KEENTOOLS_CORE_STATUS"] = status
bpy.context.scene["KEENTOOLS_CORE_VERSION"] = (
    f"{version.major}.{version.minor}.{version.patch}"
)
bpy.ops.wm.save_userpref()
print({
    "status": status,
    "version": bpy.context.scene["KEENTOOLS_CORE_VERSION"],
    "package": str(PACKAGE),
    "progress": state,
})
