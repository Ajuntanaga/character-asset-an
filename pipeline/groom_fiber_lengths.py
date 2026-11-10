"""V625: stagger fiber tips along their existing shared curl trajectories."""
import numpy as np


def stagger_tips(points, radii, rng):
    """Shorten children without changing roots, guide shape or root radii.

    Resample each child over a different prefix of its trajectory. Rebuild its
    taper over that prefix so the new tip remains fine rather than cut blunt.
    """
    count, steps, _ = points.shape
    lengths = rng.uniform(.68, 1., count)
    # Retain a minority of full-length strands to preserve the guide envelope.
    lengths[rng.random(count) < .12] = 1.
    parameter = lengths[:, None] * np.linspace(0., steps - 1, steps)[None, :]
    lower = np.floor(parameter).astype(np.int32)
    upper = np.minimum(lower + 1, steps - 1)
    fraction = (parameter - lower)[..., None]
    rows = np.arange(count)[:, None]
    result = points[rows, lower] * (1. - fraction) + points[rows, upper] * fraction
    return result.astype(points.dtype), radii.copy(), lengths
