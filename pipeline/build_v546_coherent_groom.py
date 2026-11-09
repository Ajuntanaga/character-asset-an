"""Reversible reference curl-flow trial, independent of the unfinished hand fit."""
import json
from pathlib import Path
import bpy
from build_v544_reference_groom import build as build_groom
from refine_v548_hairline import build as feather_hairline


def build(output):
    assert Path(bpy.data.filepath).name == 'current-v544.blend'
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = build_groom(Path(__file__).resolve().parents[1], out, coherent=True)
    report['hairline'] = feather_hairline(out)
    report['status'] = 'TRIAL_REQUIRES_VISUAL_AND_DEFORMATION_REVIEW'
    path = out / 'Character_An_coherent_groom_TRIAL_v546.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report['output'] = path.name
    (out / 'build-report.json').write_text(json.dumps(report, indent=2))
    return report
