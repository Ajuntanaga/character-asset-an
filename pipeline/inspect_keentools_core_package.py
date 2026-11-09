from pathlib import Path

from keentools.blender_independent_packages.pykeentools_loader import (
    MINIMUM_VERSION_REQUIRED,
    installation_status,
    os_name,
    core_filename_info,
)
from keentools.blender_independent_packages.pykeentools_loader.config import pkt_installation_dir
from keentools.preferences.progress import InstallationProgress

package = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "third_party/keentools/packages/keentools-core-2026.3.1-linux.zip"
)
print({
    "package": str(package),
    "filename_info": core_filename_info(str(package)),
    "required": MINIMUM_VERSION_REQUIRED,
    "os": os_name(),
    "installation_dir": pkt_installation_dir(),
    "installation_status": installation_status(force_recheck=True),
    "progress": InstallationProgress.get_state(),
})
