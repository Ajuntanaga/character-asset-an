"""Build the V544 reference revision from the pinned V543 working scene."""
import json
from pathlib import Path
import sys
import bpy


def build(output):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'pipeline'))
    from build_v544_reference_groom import build as build_groom
    from build_v544_reference_eyelids import build as build_eyelids

    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    assert Path(bpy.data.filepath).name == 'current-v543.blend'
    report = {'source': 'current-v543.blend', 'quality_status': 'TRIAL_REQUIRES_VISUAL_REVIEW'}
    report['groom'] = build_groom(root, out)
    report['eyelids'] = build_eyelids(root, out)

    material = bpy.data.materials['V356_GRAYBURST_FLAMED_MAPLE']
    shader = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    stain = material.node_tree.nodes['V387_GrayStain']
    report['guitar_before'] = {
        k: shader.inputs[k].default_value
        for k in ('Roughness', 'Coat Weight', 'Coat Roughness')
    }
    report['guitar_before']['stain'] = list(stain.inputs[2].default_value)
    shader.inputs['Roughness'].default_value = .44
    shader.inputs['Coat Weight'].default_value = .04
    shader.inputs['Coat Roughness'].default_value = .38
    # Reduce gloss and stain contrast; reference fidelity still needs visual review.
    stain.inputs[2].default_value = (.52, .55, .52, 1.)
    report['guitar_after'] = {'roughness': .44, 'coat': .04, 'coat_roughness': .38,
                             'stain': [.52, .55, .52, 1.]}
    report['main_drivers'] = len(rig.animation_data.drivers)
    assert report['main_drivers'] == 1957
    bpy.context.view_layer.update()
    bpy.context.scene.render.use_persistent_data = False
    path = out / 'Character_An_reference_revision_TRIAL_v544.blend'
    # Save before the remote runner reduces render subdivision for previews.
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report['output'] = path.name
    (out / 'build-report.json').write_text(json.dumps(report, indent=2))
    return report
