"""Ordered correspondence between an open sleeve rail and a closed cuff rim."""
from bisect import bisect_right
from math import dist


def ordered_rim_points(rail, rim):
    edges = list(zip(rim, rim[1:] + rim[:1]))
    cumulative = [0.0]
    for a, b in edges:
        cumulative.append(cumulative[-1] + dist(a, b))
    perimeter = cumulative[-1]
    assert perimeter > 0 and all(b > a for a, b in zip(cumulative, cumulative[1:]))
    nearest = []
    for point in rail:
        candidates = []
        for j, (a, b) in enumerate(edges):
            delta = [y-x for x, y in zip(a, b)]
            t = max(0., min(1., sum((p-x)*d for p, x, d in zip(point, a, delta))
                           / sum(d*d for d in delta)))
            q = [x+t*d for x, d in zip(a, delta)]
            candidates.append((dist(point, q),
                               (cumulative[j]+t*(cumulative[j+1]-cumulative[j]))/perimeter))
        nearest.append(min(candidates)[1])
    unwrapped = [nearest[0]]
    for previous, current in zip(nearest, nearest[1:]):
        unwrapped.append(unwrapped[-1] + (current-previous+.5) % 1.-.5)
    span = unwrapped[-1]-unwrapped[0]
    assert .05 < abs(span) < 1., 'Sleeve rail must cover one open arc of the cuff'
    source_lengths = [0.0]
    for a, b in zip(rail, rail[1:]):
        source_lengths.append(source_lengths[-1]+dist(a, b))
    assert all(b > a for a, b in zip(source_lengths, source_lengths[1:]))
    parameters = [unwrapped[0]+span*s/source_lengths[-1] for s in source_lengths]
    mapped = []
    for parameter in parameters:
        distance = (parameter % 1.)*perimeter
        j = min(bisect_right(cumulative, distance)-1, len(edges)-1)
        t = (distance-cumulative[j])/(cumulative[j+1]-cumulative[j])
        a, b = edges[j]
        mapped.append([x+(y-x)*t for x, y in zip(a, b)])
    return mapped, {'method': 'source_arc_length_between_unwrapped_endpoint_matches',
                    'rim_turn_span': span, 'rim_parameters_unwrapped': parameters}
