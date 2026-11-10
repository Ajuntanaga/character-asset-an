"""Project native donor coordinates onto the attributed Antonia forearm atlas."""
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


class ForearmUV:
    def __init__(self):
        path = Path(__file__).resolve().parents[1] / 'github_assets/antonia-hand/forearm-uv.json'
        triangles = json.loads(path.read_text())['triangles']
        # Shared position AND UV identifies connectivity without crossing atlas seams.
        parents = list(range(len(triangles)))
        def root(i):
            while parents[i] != i:
                parents[i] = parents[parents[i]]
                i = parents[i]
            return i
        seen = {}
        for i, triangle in enumerate(triangles):
            for position, uv in zip(triangle['positions'], triangle['uv']):
                key = tuple(position + uv)
                if key in seen:
                    parents[root(i)] = root(seen[key])
                else:
                    seen[key] = i
        groups = {}
        for i, triangle in enumerate(triangles):
            groups.setdefault(root(i), []).append(triangle)
        self.charts = []
        for group in groups.values():
            positions = [Vector(p) for t in group for p in t['positions']]
            uvs = [Vector((*uv, 0)) for t in group for uv in t['uv']]
            tree = BVHTree.FromPolygons(positions, [tuple(range(i, i + 3)) for i in range(0, len(positions), 3)], all_triangles=True)
            self.charts.append((tree, positions, uvs))

    def sample(self, point, chart, hint=None):
        tree, positions, uvs = self.charts[chart]
        hit = tree.find_nearest(point)
        hits = tree.find_nearest_range(point, hit[3] + 1e-6) if hint is not None else [hit]
        samples = []
        for nearest, _, index, distance in hits:
            offset = index * 3
            uv = barycentric_transform(nearest, *positions[offset:offset + 3], *uvs[offset:offset + 3])
            samples.append((uv.xy, distance))
        return min(samples, key=lambda sample: (sample[0] - hint).length) if hint is not None else samples[0]

    def chart_for(self, point, uv):
        candidates = [(self.sample(point, i, uv), i) for i in range(len(self.charts))]
        # The wrist must already lie on this source and match its atlas mapping.
        candidates = [(value, i) for value, i in candidates if value[1] < 1e-5]
        assert candidates, 'Wrist is outside the native source patch'
        (mapped, distance), index = min(candidates, key=lambda item: (item[0][0] - uv).length)
        assert (mapped - uv).length < .005, f'Wrist source UV mismatch: point={tuple(point)} mapped={tuple(mapped)} expected={tuple(uv)} charts={len(self.charts)}'
        return index
