"""Reversible reference curl-flow trial, independent of the unfinished hand fit."""
import json
from pathlib import Path
import bpy
from build_v544_reference_groom import build as build_groom
from refine_v548_hairline import build as feather_hairline


def build(output, save=True, clean_scalp=False):
    assert Path(bpy.data.filepath).name == 'current-v544.blend'
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    scalp = None
    if clean_scalp:
        from refine_v554_scalp_surface import build as fair_scalp
        source, mask, scalp_report = fair_scalp(out)
        scalp = (source, mask)
    report = build_groom(Path(__file__).resolve().parents[1], out, coherent=True, scalp=scalp)
    report['hairline'] = feather_hairline(out, short_part=clean_scalp)
    if clean_scalp:
        report['scalp_surface'] = scalp_report
    report['status'] = 'TRIAL_REQUIRES_VISUAL_AND_DEFORMATION_REVIEW'
    path = out / 'Character_An_coherent_groom_TRIAL_v546.blend'
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report['output'] = path.name if save else None
    (out / 'build-report.json').write_text(json.dumps(report, indent=2))
    return report
