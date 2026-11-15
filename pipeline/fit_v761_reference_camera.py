"""Fit a perspective camera to the donor's known nonuniform landmark mapping.

Uses archived donor projections as correspondences, not newly detected image
landmarks. Residual error measures what a camera cannot undo in that mapping.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
source = np.asarray(json.loads((ROOT / 'production_v376_face_refinement/photo_donor_geometry.json').read_text())['vertices'])
record = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_cameras_v326.json').read_text())['three_quarter']
matrix = np.asarray(record['matrix'])
# Face surface only: exclude posterior scalp and long neck from camera fitting.
selected = (source[:, 1] < -.35) & (source[:, 2] > -.85) & (source[:, 2] < .80)
source = source[selected][::4]
target = source.copy()
target[:, 0] = source[:, 0] * .123 + .0016
target[:, 1] = source[:, 1] * .121 + .00802
target[:, 2] = np.interp(source[:, 2], [-1.72,-.85,-.30,.0515203,.33,.52,.80,.94,1.3065], [1.435,1.521,1.571,1.609121,1.645,1.670,1.709,1.732,1.795])

def rays(points, rotation, position):
    local = (points-position) @ rotation
    return local[:, :2] / -local[:, 2:3]

expected = rays(source, matrix[:3,:3], matrix[:3,3])
position = matrix[:3,3] * .123 + np.array([.0016,.00802,1.603])
x0 = np.r_[Rotation.from_matrix(matrix[:3,:3]).as_rotvec(), position]
def residual(x):
    return (rays(target, Rotation.from_rotvec(x[:3]).as_matrix(), x[3:])-expected).ravel()
fit = least_squares(residual, x0, max_nfev=300, xtol=1e-12, ftol=1e-12, gtol=1e-12)
assert fit.success and np.isfinite(fit.x).all()
rotation = Rotation.from_rotvec(fit.x[:3]).as_matrix()
assert np.all(((target-fit.x[3:]) @ rotation)[:,2] < 0)
result = np.eye(4)
result[:3,:3], result[:3,3] = rotation, fit.x[3:]
errors = np.linalg.norm(residual(fit.x).reshape(-1,2),axis=1)
output = {'status':'approximate_donor_correspondence_fit_not_image_landmark_validation', 'matrix':result.tolist(), 'camera':record['camera'], 'size':record['size'], 'image':record['image'], 'points':len(source), 'ray_residual_rms':float(np.sqrt(np.mean(errors**2))), 'ray_residual_max':float(errors.max()), 'initial_ray_residual_rms':float(np.sqrt(np.mean(np.linalg.norm(residual(x0).reshape(-1,2),axis=1)**2))), 'scope':'Neutral native face under V736 landmark remap; source donor camera held at original intrinsics; no mesh or rig edits.'}
path = ROOT/'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json'
path.write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({k:v for k,v in output.items() if k not in ('matrix','camera')}))
