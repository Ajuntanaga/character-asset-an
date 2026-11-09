"""Fit thumb opposition to the index side while preserving the current wrist."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v361_pick_cuffs'
data = json.loads((ROOT/'production_v359_hand_weights/rest_control_transforms.json').read_text())
base = json.loads((ROOT/'production_v360_hand_clearance/picking_solution.json').read_text())
bones = data['bones']
hand = np.array(base['hand_matrix_guitar']); hand[2, 3] -= .027
rest = [np.array(bones[f'FK-Finger_Thumb{i}.R']['rest']) for i in (1, 2, 3)]
links = [np.linalg.inv(bones['IK-Hand.R']['rest']) @ rest[0],
         np.linalg.inv(rest[0]) @ rest[1], np.linalg.inv(rest[1]) @ rest[2]]

def pose(a):
    matrix = hand.copy()
    points = []
    for i in range(3):
        rotation = np.eye(4)
        rotation[:3, :3] = Rotation.from_euler('xyz', [a[0], a[4], a[3]] if i == 0 else [a[i], 0, 0]).as_matrix()
        matrix = matrix @ links[i] @ rotation
        points.append(matrix[:3, 3].copy())
    points.append((matrix @ [0, bones['FK-Finger_Thumb3.R']['length'], 0, 1])[:3])
    return np.array(points)

initial = np.radians(base['fingers']['Thumb']['angles_degrees'])
target = pose(initial)[-1] + [0, .012, .003]
result = least_squares(lambda a: np.r_[(pose(a)[-1]-target)*12, (a-initial)*.0006],
                       initial, bounds=(np.radians([-65,-45,-35,-85,-85]), np.radians([90,90,90,85,85])), max_nfev=100)
report = {'angles_degrees': np.degrees(result.x).tolist(), 'points': pose(result.x).tolist(),
          'target': target.tolist(), 'hand_matrix_guitar': hand.tolist()}
(OUT/'thumb_fit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
