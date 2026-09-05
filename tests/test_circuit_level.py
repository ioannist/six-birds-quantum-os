from fractions import Fraction

import numpy as np

from sbqos import rng
from sbqos.circuit_level import (
    build_memory_circuit,
    build_memory_circuit_asymmetric,
    calibration_curve,
    degree2_detector_indices,
    degree2_features,
    detector_shots,
    estimate_model_params,
    logical_error_bits,
    nearest_candidate,
    own_null_threshold,
    pymatching_baseline,
    sigma_theta_pinv_from_single,
    w2_prime_statistic,
)


def test_detector_shots_shapes_dtypes_and_pm_one_values():
    circuit = build_memory_circuit(distance=3, rounds=2, p=Fraction(1, 200))

    dets_pm1, obs_bits = detector_shots(circuit, N=25, rng=rng(0))

    assert dets_pm1.shape == (25, circuit.num_detectors)
    assert obs_bits.shape == (25, circuit.num_observables)
    assert dets_pm1.dtype == np.int8
    assert obs_bits.dtype == np.uint8
    assert set(np.unique(dets_pm1)).issubset({-1, 1})
    assert set(np.unique(obs_bits)).issubset({0, 1})


def test_degree2_detector_indices_count_order_and_uniqueness():
    indices = degree2_detector_indices(5)

    assert len(indices) == 15
    assert indices[:5] == [(0,), (1,), (2,), (3,), (4,)]
    assert indices[5:] == [
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    ]
    assert len(set(indices)) == len(indices)


def test_degree2_features_hand_products():
    dets = np.asarray(
        [
            [1, -1, 1],
            [-1, -1, 1],
            [1, 1, -1],
        ],
        dtype=np.int8,
    )
    indices = [(0,), (2,), (0, 1), (1, 2)]

    features = degree2_features(dets, indices)

    np.testing.assert_array_equal(
        features,
        np.asarray(
            [
                [1, 1, -1, -1],
                [-1, 1, 1, -1],
                [1, -1, 1, -1],
            ],
            dtype=np.int8,
        ),
    )


def test_w2_prime_statistic_null_scale_sanity():
    circuit = build_memory_circuit(distance=3, rounds=2, p=Fraction(1, 200))
    indices = degree2_detector_indices(circuit.num_detectors)
    theta_model, sigma_single = estimate_model_params(circuit, indices, N_cal=4000, rng=rng(1))
    N = 500
    dets_pm1, _obs = detector_shots(circuit, N=N, rng=rng(2))
    theta_hat = np.asarray(degree2_features(dets_pm1, indices), dtype=float).mean(axis=0)
    stat = w2_prime_statistic(theta_hat, theta_model, sigma_theta_pinv_from_single(sigma_single, N))
    threshold = own_null_threshold(
        circuit,
        indices,
        theta_model,
        N=N,
        B=12,
        rng=rng(3),
        sigma_single=sigma_single,
    )

    assert np.isfinite(stat)
    assert np.isfinite(threshold)
    assert threshold >= 0.0
    assert stat < max(500.0, 5.0 * threshold)


def test_pymatching_baseline_logical_error_bits_shape_and_type():
    circuit = build_memory_circuit(distance=3, rounds=2, p=Fraction(1, 200))
    matching = pymatching_baseline(circuit)
    dets_pm1, obs_bits = detector_shots(circuit, N=30, rng=rng(4))

    errors = logical_error_bits(matching, dets_pm1, obs_bits)

    assert errors.shape == (30,)
    assert errors.dtype == np.bool_


def test_asymmetric_builder_matches_symmetric_shape_at_equal_parameters():
    symmetric = build_memory_circuit(distance=3, rounds=3, p=Fraction(3, 1000))
    asymmetric = build_memory_circuit_asymmetric(
        distance=3,
        rounds=3,
        after_clifford_p=Fraction(3, 1000),
        before_round_p=Fraction(3, 1000),
        before_measure_p=Fraction(3, 1000),
        after_reset_p=Fraction(3, 1000),
    )

    assert asymmetric.num_detectors == symmetric.num_detectors
    assert asymmetric.num_observables == symmetric.num_observables


def test_calibration_curve_mean_flip_monotone_for_measurement_drift():
    curve = calibration_curve(
        distance=3,
        rounds=3,
        p0=Fraction(3, 1000),
        candidate_multipliers=[1, 5, 20],
        N_curve=20_000,
        rng=rng(5),
    )

    mean_flips = [row[1] for row in curve]
    assert mean_flips == sorted(mean_flips)


def test_nearest_candidate_exact_match():
    curve = [(0.003, 0.01), (0.006, 0.02), (0.06, 0.19)]

    assert nearest_candidate(0.02, curve) == 0.006
