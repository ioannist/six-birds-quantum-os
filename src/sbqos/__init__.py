"""Six Birds Quantum OS simulation prototype package."""

import numpy as np

__all__ = ["rng"]


def rng(seed: int) -> np.random.Generator:
    """Return the deterministic project RNG for an explicit seed."""
    return np.random.Generator(np.random.PCG64(seed))
