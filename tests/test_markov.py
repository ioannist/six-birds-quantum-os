from fractions import Fraction
from types import MappingProxyType

import numpy as np
import pytest

from sbqos import rng
from sbqos.codes import Code, rep_code, surface_code
from sbqos.markov import (
    qec_markov_model,
    rep3_n1_model,
    rep3_n4_model,
    rep3_n5_model,
    rep5_n1_model,
    stationary,
)
from sbqos.moments import MomentEngine, engine_for_mode
from sbqos.noise import n1, n2, n4


def test_rep3_n1_delta_distribution_exact():
    mm = rep3_n1_model("minimum_weight", exact=True)
    expected = (
        Fraction(6859, 8000),
        Fraction(1, 8000),
        Fraction(361, 8000),
        Fraction(19, 8000),
        Fraction(19, 8000),
        Fraction(361, 8000),
        Fraction(361, 8000),
        Fraction(19, 8000),
    )

    assert tuple(mm.P[0, :].tolist()) == expected


def test_rep3_n1_transition_matrix_exact_stochastic_and_translation_invariant():
    mm = rep3_n1_model("minimum_weight", exact=True)

    for row in mm.P:
        assert sum(row.tolist(), Fraction(0)) == Fraction(1)

    gen = rng(0)
    for _ in range(10):
        i = int(gen.integers(0, mm.P.shape[0]))
        j = int(gen.integers(0, mm.P.shape[1]))
        assert mm.P[i, j] == mm.P[0, i ^ j]


def test_rep3_minimum_weight_lenses_hand_states():
    mm = rep3_n1_model("minimum_weight", exact=True)

    assert mm.states[0] == (0, 0, 0)
    assert mm.states[5] == (1, 0, 1)
    assert mm.lens_mode_hidden is False
    assert mm.is_absorbing is False
    assert mm.lens_syndrome[0] == 0
    assert mm.lens_decoded[0] == 0
    assert mm.lens_syndrome[5] == 2  # state (h0,h1,Zbar) = (1,0,1)
    assert mm.lens_decoded[5] == 0
    assert mm.lens_syndrome[4] == 2  # same syndrome, higher logical class
    assert mm.lens_decoded[4] == 1


def test_broken_decoder_lens_is_all_zero():
    mm = rep3_n1_model("broken", exact=True)

    np.testing.assert_array_equal(mm.lens_decoded, np.zeros(mm.P.shape[0], dtype=np.int64))


def test_rep3_stationary_converges():
    mm = rep3_n1_model("minimum_weight", exact=True)

    pi = stationary(mm.P)

    assert np.linalg.norm(pi @ np.asarray(mm.P, dtype=float) - pi, ord=1) <= 1e-12


def test_rep5_n1_model_constructs_exactly_and_stationary_converges():
    mm = rep5_n1_model("minimum_weight")

    assert mm.n_syndrome_bits == 4
    assert mm.n_logical_bits == 1
    assert len(mm.states) == 32
    assert mm.P.shape == (32, 32)
    assert mm.exact is True
    assert mm.lens_mode_hidden is False
    for row in mm.P:
        assert sum(row.tolist(), Fraction(0)) == Fraction(1)

    pi = stationary(mm.P)
    assert np.linalg.norm(pi @ np.asarray(mm.P, dtype=float) - pi, ord=1) <= 1e-12


def test_surf3_n2_delta_and_rows_float_sanity(surf3_n2_minimum_weight_model):
    mm = surf3_n2_minimum_weight_model
    delta = mm.P[0, :]

    assert abs(float(np.sum(delta)) - 1.0) <= 1e-9
    assert float(np.min(delta)) >= -1e-9
    np.testing.assert_allclose(np.sum(mm.P, axis=1), np.ones(mm.P.shape[0]), atol=1e-9)


def test_surf3_n2_single_check_marginal_matches_moment_engine(surf3_n2_minimum_weight_model):
    code = surface_code(3)
    mm = surf3_n2_minimum_weight_model
    delta = mm.P[0, :]
    r = mm.n_syndrome_bits + mm.n_logical_bits
    h0_mask = np.array([((i >> (r - 1)) & 1) == 1 for i in range(delta.shape[0])])
    marginal = float(np.sum(delta[h0_mask]))
    engine = MomentEngine(n2(Fraction(3, 100), code.n), exact=False)
    expected = (1.0 - float(engine.mean(code.checks[0]))) / 2.0

    assert abs(marginal - expected) <= 1e-9


def test_surf3_n2_stationary_converges(surf3_n2_minimum_weight_model):
    mm = surf3_n2_minimum_weight_model

    pi = stationary(mm.P)

    assert np.linalg.norm(pi @ mm.P - pi, ord=1) <= 1e-12


def test_markov_state_size_guard_raises():
    v = np.zeros(2, dtype=np.uint8)
    checks = tuple(v.copy() for _ in range(15))
    code = Code(
        name="TOO_BIG",
        n=1,
        k=1,
        checks=checks,
        logicals=(),
        meta=MappingProxyType({}),
    )
    tracked = (v.copy(),)

    with pytest.raises(ValueError, match="size guard"):
        qec_markov_model(code, n1(Fraction(0), 1), tracked, "broken", exact=True)


def test_rep3_n4_hidden_model_structure_and_lenses():
    mm = rep3_n4_model()

    assert mm.P.shape == (16, 16)
    assert len(mm.states) == 16
    assert mm.states[0] == (0, 0, 0, 0)
    assert mm.states[8] == (0, 0, 0, 1)
    assert mm.n_syndrome_bits == 2
    assert mm.n_logical_bits == 1
    assert mm.exact is False
    assert mm.lens_mode_hidden is True
    assert mm.is_absorbing is False
    np.testing.assert_allclose(np.sum(mm.P, axis=1), np.ones(16), atol=1e-9)

    for sc in range(8):
        assert mm.lens_syndrome[sc] == mm.lens_syndrome[sc + 8]
        assert mm.lens_decoded[sc] == mm.lens_decoded[sc + 8]


def test_rep3_n4_hidden_transition_factorization_spot_check():
    code = rep_code(3)
    model = n4(Fraction(1, 50), Fraction(1, 50), code.n)
    mm = qec_markov_model(code, model, code.logicals[1:], "minimum_weight", exact=True)
    n_sc = 8
    basis = code.checks + code.logicals[1:]
    delta_0 = _delta_distribution_for_mode_via_engine(code.n, basis, model, mode=0, exact=True)
    delta_1 = _delta_distribution_for_mode_via_engine(code.n, basis, model, mode=1, exact=True)

    expected_mode1 = model.hidden.transition_prob * delta_1[3 ^ 5]
    expected_mode0 = (Fraction(1) - model.hidden.transition_prob) * delta_0[0]
    assert expected_mode1 == Fraction(288, 390625)
    assert expected_mode0 == Fraction(9927988, 10546875)
    assert mm.P[3, n_sc + 5] == expected_mode1
    assert mm.P[0, 0] == expected_mode0


def test_rep3_n5_hidden_model_structure_lenses_and_absorption():
    mm = rep3_n5_model()

    assert mm.P.shape == (16, 16)
    assert len(mm.states) == 16
    assert mm.n_syndrome_bits == 2
    assert mm.n_logical_bits == 1
    assert mm.exact is False
    assert mm.lens_mode_hidden is True
    assert mm.is_absorbing is True
    np.testing.assert_allclose(np.sum(mm.P, axis=1), np.ones(16), atol=1e-9)

    for sc in range(8):
        assert mm.lens_syndrome[sc] == mm.lens_syndrome[sc + 8]
        assert mm.lens_decoded[sc] == mm.lens_decoded[sc + 8]

    assert np.all(np.sum(mm.P[8:16, 0:8], axis=1) < 1e-12)


def test_hidden_markov_state_size_guard_raises():
    v = np.zeros(2, dtype=np.uint8)
    checks = tuple(v.copy() for _ in range(14))
    code = Code(
        name="TOO_BIG_HIDDEN",
        n=1,
        k=1,
        checks=checks,
        logicals=(),
        meta=MappingProxyType({}),
    )
    tracked = (v.copy(),)

    with pytest.raises(ValueError, match="size guard"):
        qec_markov_model(code, n4(Fraction(0), Fraction(0), 1), tracked, "broken", exact=False)


def _delta_distribution_for_mode_via_engine(
    n: int,
    basis,
    model,
    mode: int,
    exact: bool,
) -> np.ndarray:
    r = len(basis)
    n_states = 2**r
    engine = engine_for_mode(model, mode, exact=exact)
    moments = np.empty(n_states, dtype=object if exact else np.float64)
    for subset in range(n_states):
        v = np.zeros(2 * n, dtype=np.uint8)
        for i, basis_vec in enumerate(basis):
            if (subset >> (r - 1 - i)) & 1:
                v ^= basis_vec
        moments[subset] = engine.mean(v)

    out = moments.copy()
    h = 1
    while h < out.shape[0]:
        for start in range(0, out.shape[0], 2 * h):
            left = out[start : start + h].copy()
            right = out[start + h : start + 2 * h].copy()
            out[start : start + h] = left + right
            out[start + h : start + 2 * h] = left - right
        h *= 2

    if exact:
        return np.array([Fraction(1, n_states) * value for value in out], dtype=object)
    return out / float(n_states)
