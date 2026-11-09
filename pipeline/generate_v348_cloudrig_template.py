"""Generate and save the official free Sintel CloudRig as a reusable rig asset."""
import bpy
import json
from pathlib import Path

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v348_tripo_figures_cloudrig'
previous = bpy.context.scene
scene = bpy.data.scenes['V348_CLOUDRIG_TEMPLATE']
bpy.context.window.scene = scene
meta = bpy.data.objects['V348_CLOUDRIG_SINTEL_METARIG_TEMPLATE']
bpy.ops.object.select_all(action='DESELECT')
meta.hide_set(False)
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
if meta.cloudrig.generator.target_rig is None:
    bpy.ops.pose.cloudrig_generate(focus_generated=True, preserve_state=False)
rig = meta.cloudrig.generator.target_rig
if rig is None or rig.name.startswith('FAILED-'):
    raise RuntimeError('CloudRig did not generate a usable target rig')
rig.name = 'V348_CLOUDRIG_SINTEL_CONTROLS'
rig['source_url'] = 'https://extensions.blender.org/add-ons/cloudrig/'
rig['status'] = 'Official template generated; requires fitting and skinning to character'
rig.show_in_front = True
deform_bones = [b.name for b in rig.data.bones if b.use_deform]
report = {
    'addon': 'CloudRig 2.2.31', 'template': 'META-Sintel',
    'generated_object': rig.name, 'bone_count': len(rig.data.bones),
    'deform_bone_count': len(deform_bones), 'deform_bones': deform_bones,
    'bone_collections': [c.name for c in rig.data.collections_all],
    'character_bound': False,
}
path = OUT / 'CloudRig_Sintel_Control_Rig.blend'
bpy.data.libraries.write(str(path), {scene}, fake_user=True, compress=True)
report['rig_asset'] = str(path)
(OUT / 'cloudrig_generation.json').write_text(json.dumps(report, indent=2))
bpy.context.window.scene = previous
print(json.dumps({k: v for k, v in report.items() if k != 'deform_bones'}))
