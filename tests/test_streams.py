from fractions import Fraction

import numpy as np
import stim
import pytest

import sbqos.streams as streams_module
from sbqos import rng
from sbqos.codes import rep_code, surface_code
from sbqos.moments import MomentEngine, ProbeFamily, degree2_family
from sbqos.noise import n1, n2, n4, n5
from sbqos.streams import (
    ShotTable,
    _all_commute,
    _targets_for_vec,
    build_stim_circuit,
    cusum_detect,
    cusum_null_threshold,
    degree2_model_params,
    empirical_blocks,
    omega_stat,
    qubit_logical_sensitivity,
    qubit_rate_dictionary,
    sample_shots,
    w1_witness,
    w2b_statistic,
    w2c_naming,
    w2d_shot_scores,
    w2_witness,
)
from sbqos.xi import xi_residual


def test_forced_x_error_on_middle_qubit_matches_rep3_syndrome_and_logical():
    code = rep_code(3)
    L = ProbeFamily("native", code.checks, ("h0", "h1"))
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    probes = L.vecs + D.vecs
    k = len(probes)
    assert _all_commute(probes)

    circuit = stim.Circuit()
    for vec in probes:
        circuit.append("MPP", stim.target_combined_paulis(_targets_for_vec(vec, code.n)))
    circuit.append("X_ERROR", [1], 1.0)
    for vec in probes:
        circuit.append("MPP", stim.target_combined_paulis(_targets_for_vec(vec, code.n)))
    for i in range(k):
        circuit.append("DETECTOR", [stim.target_rec(-(2 * k - i)), stim.target_rec(-(k - i))])

    dets = circuit.compile_detector_sampler(seed=0).sample(shots=5)
    outcomes = (1 - 2 * dets.astype(np.int8)).astype(np.int8)

    np.testing.assert_array_equal(outcomes[:, :2], -np.ones((5, 2), dtype=np.int8))
    np.testing.assert_array_equal(outcomes[:, 2:], np.ones((5, 1), dtype=np.int8))


def test_anticommuting_logicals_use_classical_zero_noise_oracle_path(monkeypatch):
    code = rep_code(3)
    L = ProbeFamily("native", code.checks, ("h0", "h1"))
    D = ProbeFamily("logical", code.logicals, ("Xbar", "Zbar"))
    model = n1(Fraction(0, 1), code.n)

    assert _all_commute(code.checks)
    assert not _all_commute(code.logicals)
    monkeypatch.setattr(
        streams_module,
        "build_stim_circuit",
        lambda *args, **kwargs: pytest.fail("anticommuting probes must not use the Stim path"),
    )

    shots = sample_shots(code, model, L, D, N=50, rng=rng(0))

    assert shots.mode is None
    np.testing.assert_array_equal(shots.D_outcomes, np.ones((50, 2), dtype=np.int8))


def test_commuting_non_hidden_probe_set_uses_stim_path(monkeypatch):
    code = rep_code(3)
    model = n1(Fraction(0, 1), code.n)
    L = ProbeFamily("native", code.checks, ("h0", "h1"))
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    calls = 0
    original = streams_module.build_stim_circuit

    def wrapped_build_stim_circuit(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    assert _all_commute(L.vecs + D.vecs)
    monkeypatch.setattr(streams_module, "build_stim_circuit", wrapped_build_stim_circuit)

    shots = sample_shots(code, model, L, D, N=3, rng=rng(0))

    assert calls == 1
    assert shots.mode is None
    np.testing.assert_array_equal(shots.L_outcomes, np.ones((3, 2), dtype=np.int8))
    np.testing.assert_array_equal(shots.D_outcomes, np.ones((3, 1), dtype=np.int8))


def test_hidden_n4_and_n5_sample_shots_shapes_modes_and_pm_one_values():
    code = rep_code(3)
    L = ProbeFamily("native", code.checks, ("h0", "h1"))
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))

    for model in (n4(Fraction(1, 50), Fraction(1, 2), code.n), n5(Fraction(1, 20), Fraction(1, 2), code.n, 1)):
        shots = sample_shots(code, model, L, D, N=10, rng=rng(0))

        assert shots.mode is not None
        assert shots.mode.shape == (10,)
        assert shots.L_outcomes.shape == (10, 2)
        assert shots.D_outcomes.shape == (10, 1)
        assert set(np.unique(shots.L_outcomes)).issubset({-1, 1})
        assert set(np.unique(shots.D_outcomes)).issubset({-1, 1})


def test_build_stim_circuit_rejects_hidden_and_non_unit_rounds():
    code = rep_code(3)

    with pytest.raises(ValueError, match="rounds must be 1"):
        build_stim_circuit(code, n1(Fraction(1, 20), code.n), rounds=2)
    with pytest.raises(ValueError, match="hidden-mode"):
        build_stim_circuit(code, n4(Fraction(1, 50), Fraction(1, 50), code.n), rounds=1)


def test_empirical_blocks_tiny_toy_kdl_is_two_thirds():
    v = np.zeros(2, dtype=np.uint8)
    L = ProbeFamily("native", (v,), ("L",))
    D = ProbeFamily("logical", (v.copy(),), ("D",))
    shots = ShotTable(
        L=L,
        D=D,
        L_outcomes=np.array([[1], [1], [1], [-1]], dtype=np.int8),
        D_outcomes=np.array([[1], [1], [-1], [-1]], dtype=np.int8),
        mode=None,
    )

    blocks = empirical_blocks(shots, L, D)

    assert blocks.K_DL[0, 0] == pytest.approx(2.0 / 3.0, abs=1e-12)


def test_empirical_blocks_rejects_mismatched_probe_family_without_array_equality():
    v = np.zeros(2, dtype=np.uint8)
    L = ProbeFamily("native", (v,), ("L",))
    D = ProbeFamily("logical", (v.copy(),), ("D",))
    wrong_L = ProbeFamily("native", (v.copy(),), ("other",))
    shots = ShotTable(
        L=L,
        D=D,
        L_outcomes=np.array([[1], [-1]], dtype=np.int8),
        D_outcomes=np.array([[1], [-1]], dtype=np.int8),
        mode=None,
    )

    with pytest.raises(ValueError, match="different probe family"):
        empirical_blocks(shots, wrong_L, D)


def test_surf3_n2_empirical_blocks_converge_to_moment_model_at_five_sigma():
    code = surface_code(3)
    model = n2(Fraction(3, 100), code.n)
    L = ProbeFamily("native", code.checks, tuple(f"h{i}" for i in range(len(code.checks))))
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    N = 1_000_000
    assert _all_commute(L.vecs + D.vecs)

    shots = sample_shots(code, model, L, D, N=N, rng=rng(0))
    emp = empirical_blocks(shots, L, D)
    expected = MomentEngine(model, exact=False).cov_blocks(L, D)

    _assert_five_sigma(emp.K_LL, expected.K_LL, N)
    _assert_five_sigma(emp.K_DL, expected.K_DL, N)
    _assert_five_sigma(emp.K_DD, expected.K_DD, N)


def test_omega_stat_shape_identity_nonnegative_and_deterministic():
    code = rep_code(3)
    model = n1(Fraction(1, 20), code.n)
    L = ProbeFamily("native", code.checks, ("h0", "h1"))
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))

    omega1 = omega_stat(code, model, L, D, N=3000, B=30, rng=rng(123))
    omega2 = omega_stat(code, model, L, D, N=3000, B=30, rng=rng(123))

    assert omega1.shape == (1, 1)
    assert omega1[0, 0] >= 0.0
    np.testing.assert_allclose(omega1, np.eye(1) * omega1[0, 0])
    np.testing.assert_array_equal(omega1, omega2)


def test_w1_and_w2_witnesses_run_and_return_finite_correct_shapes():
    code = rep_code(3)
    model = n1(Fraction(1, 20), code.n)
    L = ProbeFamily("native", code.checks, ("h0", "h1"))
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    model_blocks = MomentEngine(model, exact=False).cov_blocks(L, D)
    _Xi, A_star = xi_residual(model_blocks)
    omega = omega_stat(code, model, L, D, N=1000, B=10, rng=rng(5))
    shots = sample_shots(code, model, L, D, N=5000, rng=rng(6))

    w1 = w1_witness(shots, model_blocks, omega)
    w2 = w2_witness(shots, model_blocks, A_star, omega)

    assert np.isfinite(w1.lam_max)
    assert np.isfinite(w2.lam_max)
    assert w1.z.shape == (len(D.vecs),)
    assert w2.z.shape == (len(D.vecs),)
    assert w1.labels == D.labels
    assert w2.labels == D.labels


def test_degree2_model_params_exact_fraction_outputs_and_rejects_float_engine():
    code, model, L, _D, F = _surf3_degree2_setup()

    theta, sigma = degree2_model_params(MomentEngine(model, exact=True), F, N=1000)

    assert theta.shape == (36,)
    assert all(isinstance(x, Fraction) for x in theta)
    assert sigma.shape == (36, 36)
    assert all(isinstance(sigma[idx], Fraction) for idx in np.ndindex(sigma.shape))
    with pytest.raises(ValueError, match="exact MomentEngine"):
        degree2_model_params(MomentEngine(model, exact=False), F, N=1000)


def test_w2b_statistic_mismatch_guard_and_null_sanity_bound():
    code, model, _L, D, F = _surf3_degree2_setup()
    theta, sigma = degree2_model_params(MomentEngine(model, exact=True), F, N=200000)
    shots = sample_shots(code, model, F, D, N=200000, rng=rng(101))
    wrong_F = ProbeFamily(F.role, F.vecs, tuple(f"bad{i}" for i in range(len(F.vecs))))

    with pytest.raises(ValueError, match="different L probe family"):
        w2b_statistic(shots, wrong_F, theta, sigma)

    T = w2b_statistic(shots, F, theta, sigma)
    assert np.isfinite(T)
    assert T < 200.0


def test_w2c_dictionary_names_synthetic_qubit_direction_and_logical_sensitivity_is_finite():
    code, model, L, D, F = _surf3_degree2_setup()
    theta, sigma = degree2_model_params(MomentEngine(model, exact=True), F, N=1000)
    dictionary = qubit_rate_dictionary(model, F)
    sigma_pinv = np.linalg.pinv(np.asarray(sigma, dtype=float), rcond=1e-12)

    assert set(dictionary) == set(range(code.n))
    assert all(direction.shape == (36,) for direction in dictionary.values())
    assert sum(np.linalg.norm(dictionary[q]) > 0.0 for q in range(code.n)) >= 3

    theta_hat = np.asarray(theta, dtype=float) + dictionary[4]
    named, score = w2c_naming(theta_hat, theta, sigma_pinv, dictionary)
    assert named == 4
    assert np.isfinite(score)

    for q in (0, 4):
        z = qubit_logical_sensitivity(model, q, L, D)
        assert z.shape == (2,)
        assert np.all(np.isfinite(z))
        assert np.linalg.norm(z) > 0.0


def test_w2d_scores_mismatch_guard_nonnegative_and_cusum_sanity():
    code, model, _L, D, F = _surf3_degree2_setup()
    theta, sigma_single = degree2_model_params(MomentEngine(model, exact=True), F, N=1)
    sigma_single_pinv = np.linalg.pinv(np.asarray(sigma_single, dtype=float), rcond=1e-12)
    shots = sample_shots(code, model, F, D, N=5000, rng=rng(202))
    wrong_F = ProbeFamily(F.role, F.vecs, tuple(f"bad{i}" for i in range(len(F.vecs))))

    with pytest.raises(ValueError, match="different L probe family"):
        w2d_shot_scores(shots, wrong_F, theta, sigma_single_pinv)

    scores = w2d_shot_scores(shots, F, theta, sigma_single_pinv)
    assert scores.shape == (5000,)
    assert np.all(np.isfinite(scores))
    assert float(np.min(scores)) >= -1e-9

    assert cusum_detect(np.zeros(10), baseline=1.0, threshold=1.0) is None
    assert cusum_detect(np.full(10, 101.0), baseline=1.0, threshold=10.0) is not None


def test_cusum_null_threshold_controls_independent_null_trajectories():
    code, model, _L, D, F = _surf3_degree2_setup()
    theta, sigma_single = degree2_model_params(MomentEngine(model, exact=True), F, N=1)
    sigma_single_pinv = np.linalg.pinv(np.asarray(sigma_single, dtype=float), rcond=1e-12)
    baseline, threshold = cusum_null_threshold(
        code,
        model,
        _L,
        D,
        F,
        theta,
        sigma_single_pinv,
        run_length=100,
        B=200,
        rng=rng(303),
        target_false_alarm=0.05,
    )

    triggers = 0
    for i in range(50):
        shots = sample_shots(code, model, F, D, N=100, rng=rng(1000 + i))
        scores = w2d_shot_scores(shots, F, theta, sigma_single_pinv)
        triggers += int(cusum_detect(scores, baseline, threshold) is not None)
    assert triggers <= 10


def _assert_five_sigma(empirical: np.ndarray, model: np.ndarray, N: int) -> None:
    for idx in np.ndindex(empirical.shape):
        v = float(model[idx])
        sigma = np.sqrt(max(0.0, (1.0 - v * v) / float(N)))
        assert abs(float(empirical[idx]) - v) <= 5.0 * sigma


def _surf3_degree2_setup():
    code = surface_code(3)
    model = n2(Fraction(3, 100), code.n)
    L = ProbeFamily("native", code.checks, tuple(f"h{i}" for i in range(len(code.checks))))
    D = ProbeFamily("logical", code.logicals, ("Xbar", "Zbar"))
    F = degree2_family(L)
    return code, model, L, D, F
