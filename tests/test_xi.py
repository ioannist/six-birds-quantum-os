from fractions import Fraction
from itertools import product

import numpy as np

from sbqos import rng
from sbqos.codes import rep_code, surface_code, sympl
from sbqos.moments import CovBlocks, MomentEngine, ProbeFamily
from sbqos.noise import n1, n2
from sbqos.xi import (
    _pinv,
    blind_spot_witness,
    chain_rule_check,
    discharge,
    psd_check,
    select_checks,
    xi_residual,
)


def _toy_family(label):
    return ProbeFamily("toy", (np.zeros(2, dtype=np.uint8),), (label,))


def _rep3_families():
    code = rep_code(3)
    h0, h1 = code.checks
    zbar = code.logicals[1]
    return code, h0, h1, zbar


def _xor(a, b):
    v = (a ^ b).astype(np.uint8)
    v.setflags(write=False)
    return v


def _sigma(a, e):
    return Fraction(1 if sympl(a, e) == 0 else -1)


def _x_error(n, xs):
    e = np.zeros(2 * n, dtype=np.uint8)
    for q in xs:
        e[q] = 1
    return e


def _random_nonempty_subset(gen, size):
    subset_size = int(gen.integers(1, size + 1))
    return tuple(sorted(int(i) for i in gen.choice(size, size=subset_size, replace=False)))


def _random_nonempty_proper_subset(gen, size):
    subset_size = int(gen.integers(1, size))
    return tuple(sorted(int(i) for i in gen.choice(size, size=subset_size, replace=False)))


def _fraction_matrix(rows):
    return np.array(rows, dtype=object)


def _check_penrose_and_numpy_match(K, tol=1e-9):
    G = _pinv(K)
    Kf = np.array([[float(x) for x in row] for row in K])
    Gf = np.array([[float(x) for x in row] for row in G])
    ref = np.linalg.pinv(Kf, rcond=1e-12)
    assert np.allclose(Kf @ Gf @ Kf, Kf, atol=tol)
    assert np.allclose(Gf @ Kf @ Gf, Gf, atol=tol)
    assert np.allclose(Kf @ Gf, (Kf @ Gf).T, atol=tol)
    assert np.allclose(Gf @ Kf, (Gf @ Kf).T, atol=tol)
    assert np.allclose(Gf, ref, atol=1e-6)


def test_xi_residual_toy_one_by_one_blocks():
    L = _toy_family("l0")
    D = _toy_family("d0")
    blocks = CovBlocks(
        L=L,
        D=D,
        K_LL=np.array([[1.0]]),
        K_DL=np.array([[0.5]]),
        K_DD=np.array([[1.0]]),
    )

    Xi, A_star = xi_residual(blocks)

    np.testing.assert_allclose(Xi, np.array([[0.75]]))
    np.testing.assert_allclose(A_star, np.array([[0.5]]))


def test_xi_residual_zero_variance_probe_leaves_residual_unchanged():
    L = _toy_family("l0")
    D = _toy_family("d0")
    blocks = CovBlocks(
        L=L,
        D=D,
        K_LL=np.array([[0.0]]),
        K_DL=np.array([[0.7]]),
        K_DD=np.array([[2.0]]),
    )

    Xi, _ = xi_residual(blocks)

    np.testing.assert_allclose(Xi, np.array([[2.0]]))


def test_blind_spot_witness_toy_diagonal():
    labels = ("toy0", "toy1")
    witness = blind_spot_witness(np.diag([2.0, 1.0]), np.zeros((2, 2)), labels)

    assert witness.lam_max == 2.0
    assert abs(witness.z[0]) == 1.0
    assert abs(witness.z[1]) == 0.0
    assert witness.labels == labels


def test_pinv_fraction_duplicate_rows_exact_and_penrose():
    K = _fraction_matrix(
        [
            [Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1)],
        ]
    )

    G = _pinv(K)

    assert G[0, 0] == Fraction(1, 4)
    assert G[0, 1] == Fraction(1, 4)
    assert G[1, 0] == Fraction(1, 4)
    assert G[1, 1] == Fraction(1, 4)
    _check_penrose_and_numpy_match(K)


def test_pinv_fraction_rank_two_three_by_three_penrose():
    B = _fraction_matrix(
        [
            [Fraction(1), Fraction(2)],
            [Fraction(2), Fraction(1)],
            [Fraction(1), Fraction(1)],
        ]
    )
    K = B @ B.T

    _check_penrose_and_numpy_match(K)


def test_pinv_fraction_rep3_full_rank_kll_penrose():
    _, h0, h1, zbar = _rep3_families()
    engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    blocks = engine.cov_blocks(
        ProbeFamily("native", (h0, h1), ("h0", "h1")),
        ProbeFamily("logical", (zbar,), ("Zbar",)),
    )

    _check_penrose_and_numpy_match(blocks.K_LL)


def test_rep3_n1_independence_kdl_entry_exact_zero():
    _, h0, h1, zbar = _rep3_families()
    engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    L = ProbeFamily("native", (h0, h1), ("h0", "h1"))
    D = ProbeFamily("logical", (zbar,), ("Zbar",))

    blocks = engine.cov_blocks(L, D)

    assert blocks.K_DL[0, 1] == Fraction(0)


def test_chain_rule_rep3_n1_exact():
    _, h0, h1, zbar = _rep3_families()
    engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    L = ProbeFamily("native", (h0,), ("h0",))
    D = ProbeFamily("logical", (zbar,), ("Zbar",))
    M = ProbeFamily("candidate", (h1,), ("h1",))

    assert chain_rule_check(engine, L, D, M) == 0.0


def test_chain_rule_surface3_n2_exact():
    code = surface_code(3)
    engine = MomentEngine(n2(Fraction(3, 100), code.n), exact=True)
    L = ProbeFamily("native", code.checks[:3], ("h0", "h1", "h2"))
    M = ProbeFamily("candidate", code.checks[3:], tuple(f"h{i}" for i in range(3, len(code.checks))))
    D = ProbeFamily("logical", (code.logicals[0],), ("Xbar",))

    assert chain_rule_check(engine, L, D, M) == 0.0


def test_discharge_saturation_duplicate_exact_zero():
    _, h0, _, zbar = _rep3_families()
    engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    L = ProbeFamily("native", (h0,), ("h0",))
    D = ProbeFamily("logical", (zbar,), ("Zbar",))
    M = ProbeFamily("candidate", (h0,), ("h0_duplicate",))

    D_matrix, value = discharge(engine.extend_blocks(engine.cov_blocks(L, D), M), (0,))

    assert D_matrix[0, 0] == Fraction(0)
    assert value == 0.0


def test_xor_combination_is_not_saturated_gives_positive_discharge():
    n = 2

    def z(qubit):
        v = np.zeros(2 * n, dtype=np.uint8)
        v[n + qubit] = 1
        return v

    z0, z1 = z(0), z(1)
    z0z1 = (z0 ^ z1).astype(np.uint8)
    engine = MomentEngine(n1(Fraction(1, 2), n), exact=True)
    L = ProbeFamily("native", (z0, z1), ("Z0", "Z1"))
    D = ProbeFamily("logical", (z0z1,), ("Z0Z1",))
    M = ProbeFamily("candidate", (z0z1,), ("Z0Z1_as_candidate",))

    Xi_L, _ = xi_residual(engine.cov_blocks(L, D))
    ext = engine.extend_blocks(engine.cov_blocks(L, D), M)
    _D_matrix, value = discharge(ext, (0,))

    assert Xi_L[0, 0] == Fraction(1)
    assert value == 1.0
    assert chain_rule_check(engine, L, D, M) == 0.0


def test_psd_check_real_rep_and_surface_cases():
    _, h0, h1, zbar = _rep3_families()
    rep_engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    rep_blocks = rep_engine.cov_blocks(
        ProbeFamily("native", (h0, h1), ("h0", "h1")),
        ProbeFamily("logical", (zbar,), ("Zbar",)),
    )
    rep_Xi, _ = xi_residual(rep_blocks)

    code = surface_code(3)
    surf_engine = MomentEngine(n2(Fraction(3, 100), code.n), exact=True)
    surf_blocks = surf_engine.cov_blocks(
        ProbeFamily("native", code.checks[:3], ("h0", "h1", "h2")),
        ProbeFamily("logical", (code.logicals[0],), ("Xbar",)),
    )
    surf_Xi, _ = xi_residual(surf_blocks)

    assert psd_check(rep_Xi, tol=1e-9)
    assert psd_check(surf_Xi, tol=1e-9)


def test_select_checks_rep3_prefers_informative_candidate_over_duplicate():
    _, h0, h1, zbar = _rep3_families()
    engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    L0 = ProbeFamily("native", (h0,), ("h0",))
    D = ProbeFamily("logical", (zbar,), ("Zbar",))
    candidates = ProbeFamily("candidate", (h1, h0), ("h1", "h0_duplicate"))

    log = select_checks(
        engine,
        L0,
        D,
        candidates,
        costs=(1.0, 1.0),
        budget=10.0,
        tol_stop=1e-8,
    )

    assert log.selected_indices == (0,)
    assert log.rounds[0].selected_label == "h1"
    assert log.rounds[0].rankings[0].candidate_label == "h1"
    assert log.rounds[0].rankings[0].value > 0
    assert log.rounds[-1].selected_label is None


def test_select_checks_skips_infeasible_high_value_candidate():
    _, h0, h1, zbar = _rep3_families()
    engine = MomentEngine(n1(Fraction(1, 20), 3), exact=True)
    L0 = ProbeFamily("native", (h0,), ("h0",))
    D = ProbeFamily("logical", (zbar,), ("Zbar",))
    candidates = ProbeFamily(
        "candidate",
        (h0, h0, zbar, h1),
        ("dup0", "dup1", "expensive_zbar", "cheap_h1"),
    )

    log = select_checks(
        engine,
        L0,
        D,
        candidates,
        costs=(1.0, 1.0, 2.0, 1.0),
        budget=1.0,
        tol_stop=1e-8,
    )

    assert log.selected_indices == (3,)
    assert log.rounds[0].selected_label == "cheap_h1"
    expensive = next(r for r in log.rounds[0].rankings if r.candidate_label == "expensive_zbar")
    cheap = next(r for r in log.rounds[0].rankings if r.candidate_label == "cheap_h1")
    assert not expensive.feasible
    assert expensive.value > cheap.value
    assert cheap.feasible


def test_thm_chain_rule_rep5_seeded_splits_exact():
    code = rep_code(5)
    engine = MomentEngine(n1(Fraction(1, 20), code.n), exact=True)
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))

    for seed in range(5):
        gen = rng(seed)
        l_indices = _random_nonempty_proper_subset(gen, len(code.checks))
        m_indices = tuple(i for i in range(len(code.checks)) if i not in l_indices)
        L0 = ProbeFamily("native", tuple(code.checks[i] for i in l_indices), tuple(f"h{i}" for i in l_indices))
        M = ProbeFamily("candidate", tuple(code.checks[i] for i in m_indices), tuple(f"h{i}" for i in m_indices))

        assert chain_rule_check(engine, L0, D, M) == 0.0


def test_psd_check_twenty_random_float_families():
    for seed in range(20):
        gen = rng(seed)
        code_choice = int(gen.integers(0, 3))
        if code_choice == 0:
            code = rep_code(3)
            model = n1(Fraction(1, 20), code.n)
            D_vecs = code.logicals[1:]
            D_labels = ("Zbar",)
        elif code_choice == 1:
            code = rep_code(5)
            model = n1(Fraction(1, 20), code.n)
            D_vecs = code.logicals[1:]
            D_labels = ("Zbar",)
        else:
            code = surface_code(3)
            model = n2(Fraction(3, 100), code.n)
            D_vecs = code.logicals
            D_labels = ("Xbar", "Zbar")

        l_indices = _random_nonempty_subset(gen, len(code.checks))
        L = ProbeFamily("native", tuple(code.checks[i] for i in l_indices), tuple(f"h{i}" for i in l_indices))
        D = ProbeFamily("logical", D_vecs, D_labels)
        engine = MomentEngine(model, exact=False)
        Xi, _ = xi_residual(engine.cov_blocks(L, D))

        assert psd_check(Xi, tol=1e-9), (seed, code.name, l_indices)


def test_thm_top_ladder_rep3_mmse_matches_bruteforce_exact():
    code = rep_code(3)
    h0, h1 = code.checks
    zbar = code.logicals[1]
    h0h1 = _xor(h0, h1)
    p = Fraction(1, 20)
    engine = MomentEngine(n1(p, code.n), exact=True)
    L = ProbeFamily("native", (h0, h1, h0h1), ("h0", "h1", "h0^h1"))
    D = ProbeFamily("logical", (zbar,), ("Zbar",))

    Xi, _ = xi_residual(engine.cov_blocks(L, D))
    xi_mmse = Xi[0, 0]
    brute_mmse = _bruteforce_rep3_zbar_mmse(p, h0, h1, zbar)

    assert xi_mmse == Fraction(47291, 1715000)
    assert brute_mmse == Fraction(47291, 1715000)
    assert xi_mmse == brute_mmse


def _bruteforce_rep3_zbar_mmse(p, h0, h1, zbar):
    groups = {}
    for bits in product((0, 1), repeat=3):
        prob = Fraction(1)
        xs = []
        for q, bit in enumerate(bits):
            if bit:
                prob *= p
                xs.append(q)
            else:
                prob *= 1 - p
        e = _x_error(3, xs)
        syndrome_value = (_sigma(h0, e), _sigma(h1, e))
        groups.setdefault(syndrome_value, []).append((prob, _sigma(zbar, e)))

    mmse = Fraction(0)
    for outcomes in groups.values():
        group_prob = sum((prob for prob, _z in outcomes), Fraction(0))
        cond_mean = sum((prob * z for prob, z in outcomes), Fraction(0)) / group_prob
        mmse += sum((prob * (z - cond_mean) ** 2 for prob, z in outcomes), Fraction(0))
    return mmse
