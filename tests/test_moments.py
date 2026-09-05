from fractions import Fraction
from itertools import product

import numpy as np
import pytest

from sbqos.codes import sympl
from sbqos.moments import MomentEngine, ProbeFamily, degree2_family, engine_for_mode
from sbqos.noise import n1, n2, n3, n4, n5, sample_error
from sbqos import rng


def _pauli(n, xs=(), zs=()):
    e = np.zeros(2 * n, dtype=np.uint8)
    for q in xs:
        e[q] = 1
    for q in zs:
        e[n + q] = 1
    return e


def _xor(a, b):
    return (a ^ b).astype(np.uint8)


def _sigma(a, e):
    return Fraction(1 if sympl(a, e) == 0 else -1)


def _brute_mean(outcomes, a):
    return sum((prob * _sigma(a, e) for prob, e in outcomes), Fraction(0))


def _brute_cov(outcomes, a, b):
    return _brute_mean(outcomes, _xor(a, b)) - _brute_mean(outcomes, a) * _brute_mean(outcomes, b)


def _enumerate_n1(p, n):
    outcomes = []
    for bits in product((0, 1), repeat=n):
        prob = Fraction(1)
        xs = []
        for q, bit in enumerate(bits):
            if bit:
                prob *= p
                xs.append(q)
            else:
                prob *= 1 - p
        outcomes.append((prob, _pauli(n, xs=tuple(xs))))
    return outcomes


def _enumerate_n2(p, n):
    labels = ("I", "X", "Y", "Z")
    probs = {
        "I": 1 - p,
        "X": p / 3,
        "Y": p / 3,
        "Z": p / 3,
    }
    outcomes = []
    for pattern in product(labels, repeat=n):
        prob = Fraction(1)
        xs = []
        zs = []
        for q, label in enumerate(pattern):
            prob *= probs[label]
            if label in {"X", "Y"}:
                xs.append(q)
            if label in {"Z", "Y"}:
                zs.append(q)
        outcomes.append((prob, _pauli(n, xs=tuple(xs), zs=tuple(zs))))
    return outcomes


def _enumerate_n3(p, q, n, pair):
    injection = _pauli(n, zs=pair)
    outcomes = []
    for base_prob, base_error in _enumerate_n2(p, n):
        outcomes.append((base_prob * (1 - q), base_error))
        outcomes.append((base_prob * q, _xor(base_error, injection)))
    return outcomes


def test_hand_computed_single_qubit_means_exact():
    z0 = _pauli(3, zs=(0,))
    x0 = _pauli(3, xs=(0,))
    y0 = _pauli(3, xs=(0,), zs=(0,))
    identity = _pauli(3)

    assert MomentEngine(n1(Fraction(1, 20), 3), exact=True).mean(z0) == Fraction(9, 10)

    engine = MomentEngine(n2(Fraction(3, 100), 3), exact=True)
    assert engine.mean(z0) == Fraction(24, 25)
    assert engine.mean(x0) == Fraction(24, 25)
    assert engine.mean(y0) == Fraction(24, 25)
    assert engine.mean(identity) == Fraction(1)


def test_n3_conditioning_branch_exact_against_independent_rhs():
    p = Fraction(3, 100)
    q = Fraction(1, 50)
    a = _pauli(3, zs=(0,))
    model = n3(p, q, 3, (0, 1))
    base_mean = MomentEngine(n2(p, 3), exact=True).mean(a)
    sign = Fraction(1 if sympl(a, model.injection.vec) == 0 else -1)
    expected = base_mean * ((1 - q) + q * sign)

    assert MomentEngine(model, exact=True).mean(a) == expected


def test_bruteforce_n1_means_exact():
    p = Fraction(1, 20)
    model = n1(p, 3)
    engine = MomentEngine(model, exact=True)
    outcomes = _enumerate_n1(p, 3)
    probes = (
        _pauli(3, zs=(0,)),
        _pauli(3, zs=(2,)),
        _pauli(3, zs=(0, 1)),
    )

    for a in probes:
        assert engine.mean(a) == _brute_mean(outcomes, a)


def test_bruteforce_n2_means_and_cov_exact():
    p = Fraction(3, 100)
    model = n2(p, 3)
    engine = MomentEngine(model, exact=True)
    outcomes = _enumerate_n2(p, 3)
    probes = (
        _pauli(3, xs=(0,)),
        _pauli(3, zs=(2,)),
        _pauli(3, xs=(0,), zs=(1,)),
    )

    for a in probes:
        assert engine.mean(a) == _brute_mean(outcomes, a)

    a = _pauli(3, xs=(0,))
    b = _pauli(3, zs=(1,))
    assert engine.cov(a, b) == _brute_cov(outcomes, a, b)


def test_bruteforce_n3_mixture_exact():
    p = Fraction(3, 100)
    q = Fraction(1, 50)
    model = n3(p, q, 3, (0, 1))
    engine = MomentEngine(model, exact=True)
    outcomes = _enumerate_n3(p, q, 3, (0, 1))
    probes = (
        _pauli(3, xs=(0,)),
        _pauli(3, xs=(0, 1)),
    )

    for a in probes:
        assert engine.mean(a) == _brute_mean(outcomes, a)


def test_cov_blocks_and_extend_blocks_shapes_and_entries():
    engine = MomentEngine(n2(Fraction(3, 100), 3), exact=True)
    L = ProbeFamily("native", (_pauli(3, zs=(0,)), _pauli(3, zs=(1,))), ("Z0", "Z1"))
    D = ProbeFamily("logical", (_pauli(3, xs=(0,)),), ("X0",))
    M = ProbeFamily("candidate", (_pauli(3, zs=(2,)),), ("Z2",))

    blocks = engine.cov_blocks(L, D)
    ext = engine.extend_blocks(blocks, M)

    assert ext.K_MM.shape == (len(M.vecs), len(M.vecs))
    assert ext.K_DM.shape == (len(D.vecs), len(M.vecs))
    assert ext.K_ML.shape == (len(M.vecs), len(L.vecs))
    assert ext.K_MM[0, 0] == engine.cov(M.vecs[0], M.vecs[0])
    assert ext.K_DM[0, 0] == engine.cov(D.vecs[0], M.vecs[0])
    assert ext.K_ML[0, 0] == engine.cov(M.vecs[0], L.vecs[0])
    assert ext.K_ML[0, 1] == engine.cov(M.vecs[0], L.vecs[1])


def test_degree2_family_appends_xor_probe_and_label():
    a = _pauli(3, zs=(0,))
    b = _pauli(3, zs=(1,))
    family = ProbeFamily("native", (a, b), ("Z0", "Z1"))

    extended = degree2_family(family)

    assert extended.role == "native"
    assert len(extended.vecs) == 3
    np.testing.assert_array_equal(extended.vecs[2], (a + b) % 2)
    assert extended.labels == ("Z0", "Z1", "Z0^Z1")


def test_engine_for_mode_n4_matches_declared_mode_models_exact():
    p0 = Fraction(1, 50)
    model = n4(p0, Fraction(1, 50), 3)
    a = _pauli(3, zs=(0,))

    mode0 = engine_for_mode(model, 0, exact=True)
    mode1 = engine_for_mode(model, 1, exact=True)

    assert mode0.mean(a) == MomentEngine(n2(p0, 3), exact=True).mean(a)
    assert mode1.mean(a) == MomentEngine(n2(3 * p0, 3), exact=True).mean(a)


def test_moment_engine_rejects_top_level_hidden_models():
    with pytest.raises(ValueError, match="engine_for_mode"):
        MomentEngine(n4(Fraction(1, 50), Fraction(1, 50), 3), exact=True)
    with pytest.raises(ValueError, match="engine_for_mode"):
        MomentEngine(n5(Fraction(1, 20), Fraction(1, 100), 3, leak_qubit=1), exact=True)


def test_n5_hidden_spec_and_sample_error_preserves_mode_state():
    model = n5(Fraction(1, 20), Fraction(1, 100), 3, leak_qubit=1)

    assert model.hidden.kind == "latching"
    assert model.hidden.transition_prob == Fraction(1, 100)
    assert model.hidden.latch_qubit == 1
    assert model.hidden.mode_models[1].per_qubit[1] == (
        Fraction(1, 4),
        Fraction(1, 4),
        Fraction(1, 4),
        Fraction(1, 4),
    )

    e, mode_state = sample_error(model, rng(0), mode_state=1)
    assert e.shape == (6,)
    assert e.dtype == np.uint8
    assert mode_state == 1


def test_sample_error_n3_applies_single_forced_injection():
    model = n3(Fraction(0), Fraction(1), 3, (0, 1))

    e, mode_state = sample_error(model, rng(0))

    np.testing.assert_array_equal(e, _pauli(3, zs=(0, 1)))
    assert mode_state is None


def test_sample_error_rejects_mode_state_for_non_hidden_models():
    for model in (
        n1(Fraction(0), 3),
        n2(Fraction(0), 3),
        n3(Fraction(0), Fraction(0), 3, (0, 1)),
    ):
        with pytest.raises(ValueError, match="mode_state must be None"):
            sample_error(model, rng(0), mode_state=0)


def test_n4_transition_prob_one_alternates_modes_deterministically():
    model = n4(Fraction(0), Fraction(1), 3)
    gen = rng(0)
    mode = 0
    modes = []

    for _ in range(4):
        _, mode = sample_error(model, gen, mode_state=mode)
        modes.append(mode)

    assert modes == [1, 0, 1, 0]


def test_n4_transition_prob_zero_stays_put_deterministically():
    model = n4(Fraction(0), Fraction(0), 3)

    for start_mode in (0, 1):
        gen = rng(start_mode)
        mode = start_mode
        modes = []
        for _ in range(4):
            _, mode = sample_error(model, gen, mode_state=mode)
            modes.append(mode)
        assert modes == [start_mode] * 4


def test_n5_transition_prob_one_latches_then_absorbs_deterministically():
    model = n5(Fraction(0), Fraction(1), 3, leak_qubit=1)
    gen = rng(0)
    mode = 0
    modes = []

    for _ in range(4):
        _, mode = sample_error(model, gen, mode_state=mode)
        modes.append(mode)

    assert modes == [1, 1, 1, 1]


def test_n5_transition_prob_zero_never_latches_deterministically():
    model = n5(Fraction(0), Fraction(0), 3, leak_qubit=1)
    gen = rng(0)
    mode = 0
    modes = []

    for _ in range(4):
        _, mode = sample_error(model, gen, mode_state=mode)
        modes.append(mode)

    assert modes == [0, 0, 0, 0]
