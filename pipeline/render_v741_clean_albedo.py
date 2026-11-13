"""Compare a separate cleaned atlas without saving changes to the scene."""
from pathlib import Path
import hashlib
import runpy

texture = Path('references/derived/clean_albedo_v741/Character_An_clean_albedo_TRIAL_v741.png')
assert hashlib.sha256(texture.read_bytes()).hexdigest() == 'e79c9a7cb406c104301102a2d131ba2d5a1fa15992c7846957d1a17ddee7bc1e'
runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
    init_globals={'TEXTURE_PATH': str(texture),
                  'TEXTURE_SOURCE_NAME': 'Character_An_photoreal_head_basecolor_v326.png',
                  'TAG': 'v741_clean_albedo',
                  'VIEWS': ['front', 'three_quarter_reference_side']})
