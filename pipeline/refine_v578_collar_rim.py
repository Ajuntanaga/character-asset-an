"""Correct the isolated pale rear collar rim without repainting the neck."""
import json
from pathlib import Path


def build(output):
    import bpy
    from mathutils import Vector

    root = Path(__file__).resolve().parents[1]
    mask_path = root / 'github_assets/v578-collar-rim-mask.json'
    mask = json.loads(mask_path.read_text())
    body = bpy.data.objects[mask['body']]
    mesh = body.data
    basis = mesh.shape_keys.key_blocks['Basis']
    target = list(mesh.materials).index(
        bpy.data.materials['V561_MATTE_CHARCOAL_CHECK_JACKET'])
    previous, maximum = {}, 0.
    for face_id, *expected in mask['faces']:
        face = mesh.polygons[face_id]
        center = sum((body.matrix_world @ basis.data[i].co for i in face.vertices),
                     Vector()) / len(face.vertices)
        error = (center - Vector(expected)).length
        assert error < 1e-6, (face_id, error)
        maximum = max(maximum, error)
        material = mesh.materials[face.material_index]
        assert material and material.name.startswith(('V549_', 'V563_')), material
        previous[str(face_id)] = face.material_index
    assert len(previous) == 18
    for face_id in previous:
        mesh.polygons[int(face_id)].material_index = target
    mesh.update()
    report = {'assigned_faces': len(previous), 'mask': str(mask_path.relative_to(root)),
              'material': mesh.materials[target].name, 'max_centroid_error_m': maximum,
              'previous_assignments': previous,
              'status': 'TRIAL_REQUIRES_FRONT_OBLIQUE_REAR_COLLAR_REVIEW'}
    (Path(output) / 'collar-rim-report.json').write_text(json.dumps(report, indent=2))
    return {key: value for key, value in report.items() if key != 'previous_assignments'}
