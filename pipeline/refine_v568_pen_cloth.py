"""Keep the scanned metal pen while removing its rectangular cloth halo."""
import json
from pathlib import Path


def build(output):
    import bpy
    from mathutils import Vector

    root = Path(__file__).resolve().parents[1]
    mask = json.loads((root / 'github_assets/v568-pen-cloth-mask.json').read_text())
    body = bpy.data.objects[mask['body']]
    mesh = body.data
    basis = mesh.shape_keys.key_blocks['Basis']
    jacket_slots = [i for i, material in enumerate(mesh.materials)
                    if material and material.name == 'V561_MATTE_CHARCOAL_CHECK_JACKET']
    assert len(jacket_slots) == 1
    jacket = jacket_slots[0]
    assert mesh.materials[0].name.startswith('tripo_material_')
    previous, changes, max_error = {}, {}, 0.
    for face_id, label, *expected in mask['faces']:
        face = mesh.polygons[face_id]
        center = sum((body.matrix_world @ basis.data[i].co for i in face.vertices),
                     Vector()) / len(face.vertices)
        error = (center - Vector(expected)).length
        assert error < 1e-6, (face_id, error)
        assert label in (0, 1)
        assert face.material_index in (0, jacket), face.material_index
        max_error = max(max_error, error)
        previous[str(face_id)] = face.material_index
        changes[face_id] = 0 if label == 0 else jacket
    assert len(changes) == mask['cloth_face_count'] + mask['pen_face_count']
    for face_id, material_id in changes.items():
        mesh.polygons[face_id].material_index = material_id
    mesh.update()
    report = {'body': body.name, 'cloth_faces': mask['cloth_face_count'],
              'pen_faces': mask['pen_face_count'],
              'changed_faces': sum(previous[str(i)] != material for i, material in changes.items()),
              'max_centroid_error_m': max_error,
              'previous_assignments': previous,
              'status': 'TRIAL_REQUIRES_CLOTH_AND_PEN_RENDER_REVIEW'}
    (Path(output) / 'pen-cloth-material-report.json').write_text(json.dumps(report, indent=2))
    return {key: value for key, value in report.items() if key != 'previous_assignments'}
