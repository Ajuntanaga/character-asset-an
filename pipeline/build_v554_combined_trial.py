"""Combine reference corrections for whole-character review; retain V544 hands."""
import json
from pathlib import Path
import bpy


def build(output, delit_face=False):
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    from build_v546_coherent_groom import build as build_groom
    from build_v547_blink_alignment import build as build_eyes
    from refine_v550_maple_density import build as build_guitar

    report = {'groom': build_groom(out, save=False, clean_scalp=True)}
    report['eyes'] = build_eyes(root, out)
    report['guitar'] = build_guitar(out, save=False)
    if delit_face:
        from refine_v555_face_albedo import build as build_face
        report['face_albedo'] = build_face(out)

    original = bpy.data.materials['V379_DARK_COTTON_JACKET']
    jacket = original.copy()
    jacket.name = 'V554_CHARCOAL_JACKET_VARIATION'
    high = jacket.node_tree.nodes['V388_CharcoalAlbedo'].color_ramp.elements[1]
    previous = list(high.color)
    high.color = (.045, .050, .048, 1)
    affected = []
    for obj in bpy.context.scene.objects:
        for slot in obj.material_slots:
            if slot.material == original:
                slot.material = jacket
                affected.append(obj.name)
    assert affected
    report['jacket'] = {'material': jacket.name, 'original': original.name,
                        'previous_light_albedo': previous,
                        'trial_light_albedo': list(high.color),
                        'objects': sorted(set(affected))}
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    report['main_drivers'] = 1957
    report['hands'] = 'V544_UNCHANGED_UNRESOLVED'
    report['status'] = 'COMBINED_TRIAL_REQUIRES_VISUAL_AND_DEFORMATION_REVIEW'
    path = out / 'Character_An_combined_reference_TRIAL_v554.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report['output'] = path.name
    (out / 'combined-trial-report.json').write_text(json.dumps(report, indent=2))
    return report
