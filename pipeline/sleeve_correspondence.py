"""Ordered correspondence between an open sleeve rail and a closed cuff rim."""
from bisect import bisect_right
from math import dist, exp


def smooth_open_rail(rail, radius=.012):
    """Filter mesh-edge stair steps in metres, preserving the open endpoints."""
    lengths = [0.0]
    for a, b in zip(rail, rail[1:]):
        lengths.append(lengths[-1] + dist(a, b))
    result = []
    for i, point in enumerate(rail):
        window = min(radius, lengths[i], lengths[-1] - lengths[i])
        if window <= 1e-9:
            result.append(list(point))
            continue
        weights = [max(0., 1. - abs(s-lengths[i])/window) for s in lengths]
        # Arc-length quadrature avoids bias toward densely tessellated folds.
        weights = [w * (lengths[min(j+1, len(rail)-1)] - lengths[max(0, j-1)])
                   for j, w in enumerate(weights)]
        total = sum(weights)
        result.append([sum(w*p[k] for w, p in zip(weights, rail))/total
                       for k in range(3)])
    return result


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
    linear = [unwrapped[0]+span*s/source_lengths[-1] for s in source_lengths]
    # Preserve local proximity instead of sweeping uniformly around the rim.
    # Weighted isotonic regression removes reversals without crossing rails.
    sign = 1. if span > 0 else -1.
    low, high = sign*unwrapped[0], sign*unwrapped[-1]
    blocks = []
    for i, value in enumerate(unwrapped):
        weight = source_lengths[min(i+1, len(rail)-1)] - source_lengths[max(0, i-1)]
        value = max(low, min(high, sign*value))
        blocks.append([i, i+1, weight, weight*value])
        while len(blocks) > 1 and blocks[-2][3]/blocks[-2][2] > blocks[-1][3]/blocks[-1][2]:
            right = blocks.pop()
            left = blocks.pop()
            blocks.append([left[0], right[1], left[2]+right[2], left[3]+right[3]])
    fitted = [0.] * len(rail)
    for start, end, weight, total in blocks:
        fitted[start:end] = [sign*total/weight] * (end-start)
    # A small arc-length component keeps strictly positive cell widths.
    parameters = [.9*a+.1*b for a, b in zip(fitted, linear)]
    mapped = []
    for parameter in parameters:
        distance = (parameter % 1.)*perimeter
        j = min(bisect_right(cumulative, distance)-1, len(edges)-1)
        t = (distance-cumulative[j])/(cumulative[j+1]-cumulative[j])
        a, b = edges[j]
        mapped.append([x+(y-x)*t for x, y in zip(a, b)])
    return mapped, {'method': 'monotone_nearest_rim_with_ten_percent_arc_length',
                    'rim_turn_span': span, 'rim_parameters_unwrapped': parameters}


def smooth_rail_vectors(rail, vectors, radius=.012):
    """Arc-length Gaussian average; keep cancellation instead of renormalizing."""
    lengths = [0.0]
    for a, b in zip(rail, rail[1:]):
        lengths.append(lengths[-1] + dist(a, b))
    quadrature = [lengths[min(j+1, len(rail)-1)] - lengths[max(0, j-1)]
                  for j in range(len(rail))]
    result = []
    for position in lengths:
        weights = [exp(-.5*((s-position)/radius)**2)*q
                   for s, q in zip(lengths, quadrature)]
        total = sum(weights)
        result.append([sum(w*v[k] for w, v in zip(weights, vectors))/total
                       for k in range(3)])
    return result
