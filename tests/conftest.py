import pytest

from sbqos.markov import surf3_n2_model


@pytest.fixture(scope="session")
def surf3_n2_minimum_weight_model():
    return surf3_n2_model("minimum_weight", exact=False)
