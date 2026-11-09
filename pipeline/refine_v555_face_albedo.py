"""Trial de-lit albedo on the established photo UV; retain original materials."""
import hashlib
import json
from pathlib import Path
import bpy


def build(output):
    root = Path(__file__).resolve().parents[1]
    asset = root / 'assets/generated/face_delit_v555'
    source = json.loads((asset / 'SOURCE.json').read_text())
    path = asset / source['image']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert body.data.uv_layers.get('V377_FacePhotoProjection')
    original = bpy.data.materials['V549_REFERENCE_PHOTO_SKIN_BALANCED']
    material = original.copy()
    material.name = 'V555_DELIT_FACE_PREVIEW'
    nodes = material.node_tree.nodes
    texture = nodes['V377_FittedPhotoAlbedo']
    previous_image = texture.image.name
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = 'sRGB'
    image.pack()
    texture.image = image
    # Restoring the original mask avoids exposing more of the lower-quality
    # Tripo atlas beneath the fitted photo. No UV or anatomical changes.
    gain = nodes['V549_PhotoSkinBlendGain']
    previous_gain = gain.inputs[1].default_value
    gain.inputs[1].default_value = 1.
    slots = []
    for i, slot in enumerate(body.material_slots):
        if slot.material == original:
            slot.material = material
            slots.append(i)
    assert slots
    report = {'status': 'LOW_RESOLUTION_ALBEDO_TRIAL_REQUIRES_RENDER_REVIEW',
              'material': material.name, 'original_material': original.name,
              'previous_image': previous_image, 'trial_image': image.name,
              'image_dimensions': list(image.size), 'sha256': source['sha256'],
              'previous_gain': previous_gain, 'trial_gain': 1.,
              'material_slots': slots, 'uv_unchanged': True,
              'geometry_unchanged': True, 'image_packed': bool(image.packed_file)}
    (Path(output) / 'face-albedo-report.json').write_text(json.dumps(report, indent=2))
    return report
