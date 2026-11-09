"""Reassign the scanned rear collar above the old horizontal material cutoff."""
import json
from pathlib import Path


def build(output):
    import bpy
    from mathutils import Vector

    root = Path(__file__).resolve().parents[1]
    mask = json.loads((root / 'github_assets/v567-rear-collar-mask.json').read_text())
    body = bpy.data.objects[mask['body']]
    mesh = body.data
    basis = mesh.shape_keys.key_blocks['Basis']
    materials = mesh.materials
    targets = [i for i, material in enumerate(materials)
               if material and material.name == 'V561_MATTE_CHARCOAL_CHECK_JACKET']
    assert len(targets) == 1, 'Expected one corrected jacket material'
    target = targets[0]
    previous, max_error = {}, 0.
    # Validate every face before changing any assignment. IDs are accompanied
    # by original world centroids so a different topology cannot be repainted.
    for face_id, *expected in mask['faces']:
        face = mesh.polygons[face_id]
        center = sum((body.matrix_world @ basis.data[i].co for i in face.vertices),
                     Vector()) / len(face.vertices)
        error = (center - Vector(expected)).length
        assert error < 1e-6, (face_id, error)
        max_error = max(max_error, error)
        material = materials[face.material_index]
        assert material and material.name.startswith(('V549_', 'V563_')), material
        previous[str(face_id)] = face.material_index
    assert len(previous) == 2436
    for face_id in previous:
        mesh.polygons[int(face_id)].material_index = target
    mesh.update()
    report = {'body': body.name, 'assigned_faces': len(previous),
              'material': materials[target].name, 'slot': target,
              'mask': 'github_assets/v567-rear-collar-mask.json',
              'max_centroid_error_m': max_error,
              'previous_assignments': previous,
              'status': 'TRIAL_REQUIRES_REAR_COLLAR_RENDER_REVIEW'}
    (Path(output) / 'rear-collar-material-report.json').write_text(json.dumps(report, indent=2))
    return {key: value for key, value in report.items() if key != 'previous_assignments'}
