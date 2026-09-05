import numpy as np

import sbqos


def test_package_import_and_rng():
    assert isinstance(sbqos.rng(0), np.random.Generator)
