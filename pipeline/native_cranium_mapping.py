"""Partially undo V739 cranial compression without moving the eye region."""
import numpy as np

START = 1.665
TOP = 1.795
OLD_REDUCTION = .055
TRIAL_REDUCTION = .035


def compress(z, reduction):
    t = np.clip((z - START) / (TOP - START), 0., 1.)
    return z - reduction * t * t * (3. - 2. * t)


def restore_upper_head(z):
    """Map existing V739 coordinates through a monotone inverse and new field."""
    z = np.asarray(z, dtype=float)
    low, high = z.copy(), z + OLD_REDUCTION
    for _ in range(32):
        middle = (low + high) * .5
        below = compress(middle, OLD_REDUCTION) < z
        low = np.where(below, middle, low)
        high = np.where(below, high, middle)
    mapped = compress((low + high) * .5, TRIAL_REDUCTION)
    return np.where(z <= START, z, mapped)
