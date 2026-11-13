"""Use the staged original photo atlas for an isolated cloud appearance review."""
from pathlib import Path
import hashlib
import runpy

texture = Path('Character_An_photoreal_head_basecolor_v326.png')
assert hashlib.sha256(texture.read_bytes()).hexdigest() == 'aa09646354554ea5c634dcbaa1083367894addc067784de6174c76e4dc1691fd'
runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
               init_globals={'TEXTURE_PATH': str(texture), 'TAG': 'v740_textured'})
