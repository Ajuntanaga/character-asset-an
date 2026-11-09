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

    from build_v557_reference_locks import reduce_skin_microrelief
    report = {'revision': 'V560', 'skin_microrelief': reduce_skin_microrelief()}
    report['groom'] = build_groom(out, save=False, clean_scalp=True)
    report['eyes'] = build_eyes(root, out)
    from refine_v558_eye_surface import build as build_eye_surface
    report['eye_surface'] = build_eye_surface(out)
    from refine_v560_reference_face_shape import build as build_face_shape
    report['face_shape'] = build_face_shape(out)
    report['guitar'] = build_guitar(out, save=False)
    if delit_face:
        from refine_v555_face_albedo import build as build_face
        report['face_albedo'] = build_face(out)

    original = bpy.data.materials['V379_DARK_COTTON_JACKET']
    jacket = original.copy()
    jacket.name = 'V559_MATTE_CHARCOAL_WOVEN_JACKET'
    ramp = jacket.node_tree.nodes['V388_CharcoalAlbedo']
    previous = [list(e.color) for e in ramp.color_ramp.elements]
    # The scan's grayscale includes broad baked light bands. Use the existing
    # rest-position cloth height for subtle albedo variation instead, retaining
    # the saturation mask that preserves the jacket's colored details.
    for link in tuple(ramp.inputs['Fac'].links):
        jacket.node_tree.links.remove(link)
    jacket.node_tree.links.new(
        jacket.node_tree.nodes['V384_Weave_height'].outputs['Color'],
        ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].color = (.008, .009, .009, 1)
    ramp.color_ramp.elements[1].color = (.018, .021, .020, 1)
    shader = jacket.node_tree.nodes['Principled BSDF']
    roughness = shader.inputs['Roughness'].links[0].from_node
    assert roughness.type == 'MATH' and roughness.operation == 'MULTIPLY_ADD'
    assert roughness.inputs[0].links[0].from_node.name == 'V384_Weave_roughness'
    previous_roughness = [roughness.inputs[i].default_value for i in (1, 2)]
    previous_specular = shader.inputs['Specular IOR Level'].default_value
    roughness.inputs[1].default_value = .12
    roughness.inputs[2].default_value = .84
    shader.inputs['Specular IOR Level'].default_value = .10
    affected = []
    for obj in bpy.context.scene.objects:
        for slot in obj.material_slots:
            if slot.material == original:
                slot.material = jacket
                affected.append(obj.name)
    assert affected
    report['jacket'] = {'material': jacket.name, 'original': original.name,
                        'previous_albedo_range': previous,
                        'trial_albedo_range': [list(e.color) for e in ramp.color_ramp.elements],
                        'albedo_source': 'V384_Weave_height',
                        'previous_roughness_remap': previous_roughness,
                        'trial_roughness_range': [.84, .96],
                        'previous_specular_ior_level': previous_specular,
                        'specular_ior_level': .10,
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
