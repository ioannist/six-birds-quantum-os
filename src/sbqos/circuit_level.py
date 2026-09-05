"""Circuit-level detector-stream witness utilities for E8 pilots.

This module is intentionally separate from the code-capacity PauliVec
machinery in streams.py. Circuit-level model moments are measured from Stim
detector samples; no closed-form MomentEngine exists for these circuits.

Ref: design/06_W2_PHASE2.md §4.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations

import numpy as np
import pymatching
import stim


def build_memory_circuit(distance: int, rounds: int, p) -> stim.Circuit:
    """Build Stim's rotated memory-Z surface-code circuit at uniform noise p."""
    return build_memory_circuit_asymmetric(distance, rounds, p, p, p, p)


def build_memory_circuit_asymmetric(
    distance: int,
    rounds: int,
    after_clifford_p,
    before_round_p,
    before_measure_p,
    after_reset_p,
) -> stim.Circuit:
    """Build Stim's rotated memory-Z circuit with independent noise channels."""
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=distance,
        rounds=rounds,
        after_clifford_depolarization=float(after_clifford_p),
        before_round_data_depolarization=float(before_round_p),
        before_measure_flip_probability=float(before_measure_p),
        after_reset_flip_probability=float(after_reset_p),
    )


def detector_shots(circuit: stim.Circuit, N: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Return detector outcomes as ±1 and observable bits as 0/1."""
    if N <= 0:
        raise ValueError("N must be positive")
    seed = int(rng.integers(0, 2**63 - 1))
    dets, obs = circuit.compile_detector_sampler(seed=seed).sample(
        shots=N,
        separate_observables=True,
    )
    dets_pm1 = (1 - 2 * dets.astype(np.int8)).astype(np.int8)
    return dets_pm1, np.asarray(obs, dtype=np.uint8)


def degree2_detector_indices(num_detectors: int) -> list[tuple[int, ...]]:
    """Return all detector singletons and unordered detector pairs."""
    if num_detectors < 0:
        raise ValueError("num_detectors must be nonnegative")
    singles = [(i,) for i in range(num_detectors)]
    pairs = list(combinations(range(num_detectors), 2))
    return singles + pairs


def degree2_features(dets_pm1: np.ndarray, indices: list[tuple[int, ...]]) -> np.ndarray:
    """Return singleton and pair-product detector features."""
    dets = np.asarray(dets_pm1, dtype=np.int8)
    if dets.ndim != 2:
        raise ValueError("dets_pm1 must be a 2D array")
    out = np.empty((dets.shape[0], len(indices)), dtype=np.int8)
    for k, idx in enumerate(indices):
        if len(idx) == 1:
            out[:, k] = dets[:, idx[0]]
        elif len(idx) == 2:
            out[:, k] = (dets[:, idx[0]] * dets[:, idx[1]]).astype(np.int8)
        else:
            raise ValueError("degree2 feature indices must have length 1 or 2")
    return out


def estimate_model_params(
    circuit: stim.Circuit,
    indices: list[tuple[int, ...]],
    N_cal: int,
    rng: np.random.Generator,
    chunk_size: int = 20_000,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate feature means and per-shot covariance under the declared circuit.

    The returned covariance is Cov(F,F) for a single shot. For an N-shot scoring
    window, callers must use Cov(F,F)/N before taking the pseudo-inverse.
    Keeping this split explicit prevents conflating calibration size N_cal with
    the scored sample size N.
    """
    if N_cal < 2:
        raise ValueError("N_cal must be at least 2")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    n_features = len(indices)
    sums = np.zeros(n_features, dtype=np.float64)
    cross = np.zeros((n_features, n_features), dtype=np.float64)
    remaining = N_cal
    while remaining:
        take = min(chunk_size, remaining)
        dets_pm1, _obs = detector_shots(circuit, take, rng)
        features = degree2_features(dets_pm1, indices)
        sums += features.sum(axis=0, dtype=np.int64)
        f64 = np.asarray(features, dtype=np.float64)
        cross += f64.T @ f64
        remaining -= take
    theta_model = sums / float(N_cal)
    sigma_single = (cross - float(N_cal) * np.outer(theta_model, theta_model)) / float(N_cal - 1)
    return theta_model, sigma_single


def w2_prime_statistic(theta_hat: np.ndarray, theta_model: np.ndarray, sigma_theta_pinv: np.ndarray) -> float:
    """Return the circuit-level degree-<=2 quadratic statistic."""
    diff = np.asarray(theta_hat, dtype=float) - np.asarray(theta_model, dtype=float)
    W = np.asarray(sigma_theta_pinv, dtype=float)
    return float(diff @ W @ diff.T)


def own_null_threshold(
    circuit: stim.Circuit,
    indices: list[tuple[int, ...]],
    theta_model: np.ndarray,
    N: int,
    B: int,
    rng: np.random.Generator,
    quantile: float = 0.99,
    sigma_single: np.ndarray | None = None,
    N_cal: int = 50_000,
) -> float:
    """Bootstrap the null threshold for the circuit-level W2' statistic."""
    if N <= 0 or B <= 0:
        raise ValueError("N and B must be positive")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be in [0, 1]")
    if sigma_single is None:
        _theta_unused, sigma_single = estimate_model_params(circuit, indices, N_cal, rng)
    sigma_theta_pinv = np.linalg.pinv(np.asarray(sigma_single, dtype=float) / float(N), rcond=1e-12)
    values = np.empty(B, dtype=float)
    for b in range(B):
        dets_pm1, _obs = detector_shots(circuit, N, rng)
        theta_hat = np.asarray(degree2_features(dets_pm1, indices), dtype=float).mean(axis=0)
        values[b] = w2_prime_statistic(theta_hat, theta_model, sigma_theta_pinv)
    return float(np.percentile(values, quantile * 100.0))


def pymatching_baseline(circuit: stim.Circuit) -> pymatching.Matching:
    """Build a pymatching decoder from Stim's decomposed detector error model."""
    return pymatching.Matching.from_detector_error_model(circuit.detector_error_model(decompose_errors=True))


def logical_error_bits(matching: pymatching.Matching, dets_pm1: np.ndarray, obs_bits: np.ndarray) -> np.ndarray:
    """Return per-shot logical-error booleans from detector and observable samples."""
    det_bits = (np.asarray(dets_pm1, dtype=np.int8) == -1).astype(np.uint8)
    obs = np.asarray(obs_bits, dtype=np.uint8)
    predicted = np.asarray(matching.decode_batch(det_bits), dtype=np.uint8)
    if predicted.ndim == 1:
        predicted = predicted.reshape((-1, 1))
    if obs.ndim == 1:
        obs = obs.reshape((-1, 1))
    if predicted.shape != obs.shape:
        raise ValueError(f"decoder output shape {predicted.shape} does not match observables {obs.shape}")
    return np.any(predicted != obs, axis=1)


def sigma_theta_pinv_from_single(sigma_single: np.ndarray, N: int) -> np.ndarray:
    """Return pinv(Cov(F,F)/N) for an N-shot empirical mean."""
    if N <= 0:
        raise ValueError("N must be positive")
    return np.linalg.pinv(np.asarray(sigma_single, dtype=float) / float(N), rcond=1e-12)


def calibration_curve(
    distance: int,
    rounds: int,
    p0,
    candidate_multipliers: list,
    N_curve: int,
    rng: np.random.Generator,
) -> list[tuple[float, float]]:
    """Return candidate before-measurement rates and mean detector flip rates."""
    if N_curve <= 0:
        raise ValueError("N_curve must be positive")
    rows = []
    for multiplier in sorted(candidate_multipliers, key=float):
        candidate_p = float(multiplier) * float(p0)
        circuit = build_memory_circuit_asymmetric(distance, rounds, p0, p0, candidate_p, p0)
        dets_pm1, _obs = detector_shots(circuit, N_curve, rng)
        rows.append((float(candidate_p), float((dets_pm1 == -1).mean())))
    return rows


def nearest_candidate(observed_mean_flip: float, curve: list[tuple[float, float]]) -> float:
    """Return the candidate rate whose calibrated detector flip rate is closest."""
    if not curve:
        raise ValueError("calibration curve must be nonempty")
    return min(curve, key=lambda row: (abs(float(row[1]) - observed_mean_flip), float(row[0])))[0]


def run_epoch_timeline(
    declared_circuit: stim.Circuit,
    truth_circuit: stim.Circuit,
    matching_static: pymatching.Matching,
    matching_oracle: pymatching.Matching,
    indices: list[tuple[int, ...]],
    theta_model: np.ndarray,
    sigma_theta_pinv_at_epoch_N: np.ndarray,
    threshold: float,
    curve: list[tuple[float, float]],
    E_total: int,
    drift_epoch: int,
    shots_per_epoch: int,
    policy: str,
    schedule_K: int | None,
    rng: np.random.Generator,
    *,
    distance: int | None = None,
    rounds: int | None = None,
    p0=None,
    recalibration_N_cal: int | None = None,
    recalibration_B: int | None = None,
    reference_cache: dict[float, tuple[stim.Circuit, pymatching.Matching, np.ndarray, np.ndarray, float]] | None = None,
    calibration_rng: np.random.Generator | None = None,
    fixed_recalibration_epochs: set[int] | None = None,
) -> dict:
    """Run one epoch-discretized closed-loop control timeline.

    The witness policy is self-correcting: after each recalibration it keeps
    monitoring, using a fresh model-parameter and threshold calibration for the
    selected candidate circuit as the new comparison target.
    """
    if E_total <= 0 or shots_per_epoch <= 0:
        raise ValueError("E_total and shots_per_epoch must be positive")
    if not 0 <= drift_epoch <= E_total:
        raise ValueError("drift_epoch must be in [0, E_total]")
    if policy not in {"static", "oracle", "scheduled", "witness"}:
        raise ValueError("policy must be static, oracle, scheduled, or witness")
    if policy == "scheduled" and fixed_recalibration_epochs is None and (schedule_K is None or schedule_K <= 0):
        raise ValueError("scheduled policy requires a positive schedule_K or fixed_recalibration_epochs")
    if fixed_recalibration_epochs is not None:
        if any(epoch < 0 or epoch >= E_total for epoch in fixed_recalibration_epochs):
            raise ValueError("fixed_recalibration_epochs must be within the timeline")

    current_matching = matching_static
    current_theta_model = np.asarray(theta_model, dtype=float).copy()
    current_sigma_pinv = np.asarray(sigma_theta_pinv_at_epoch_N, dtype=float).copy()
    current_threshold = float(threshold)
    reference_rng = calibration_rng if calibration_rng is not None else rng
    recalibration_events = 0
    first_recalibration_epoch = None
    phase = int(rng.integers(0, schedule_K)) if policy == "scheduled" and schedule_K is not None and fixed_recalibration_epochs is None else 0
    candidate_matching_cache: dict[float, tuple[stim.Circuit, pymatching.Matching]] = {}
    candidate_reference_cache = reference_cache if reference_cache is not None else {}

    policy_rates = []
    static_rates = []
    oracle_rates = []
    recalibration_epochs = []
    candidate_ps = []
    witness_stats = []

    for epoch in range(E_total):
        epoch_circuit = declared_circuit if epoch < drift_epoch else truth_circuit
        dets_pm1, obs_bits = detector_shots(epoch_circuit, shots_per_epoch, rng)
        theta_hat = _epoch_theta_hat(dets_pm1, indices)

        should_recalibrate = False
        stat = w2_prime_statistic(theta_hat, current_theta_model, current_sigma_pinv)
        if policy == "scheduled" and fixed_recalibration_epochs is not None:
            should_recalibrate = epoch in fixed_recalibration_epochs
        elif policy == "scheduled" and schedule_K is not None and (epoch - phase) % schedule_K == 0:
            should_recalibrate = True
        elif policy == "witness" and stat > current_threshold:
            should_recalibrate = True

        if should_recalibrate:
            candidate_p = _recalibrated_candidate(dets_pm1, curve)
            if candidate_p in candidate_reference_cache:
                candidate_circuit, current_matching, cached_theta, cached_sigma_pinv, cached_threshold = candidate_reference_cache[candidate_p]
            elif candidate_p not in candidate_matching_cache:
                candidate_circuit = _recalibrated_circuit(distance, rounds, p0, candidate_p)
                candidate_matching_cache[candidate_p] = (candidate_circuit, pymatching_baseline(candidate_circuit))
            if candidate_p not in candidate_reference_cache:
                candidate_circuit, current_matching = candidate_matching_cache[candidate_p]
            if policy == "witness":
                if recalibration_N_cal is None or recalibration_B is None:
                    raise ValueError("witness recalibration requires recalibration_N_cal and recalibration_B")
                if candidate_p not in candidate_reference_cache:
                    candidate_theta, candidate_sigma_single = estimate_model_params(
                        candidate_circuit,
                        indices,
                        recalibration_N_cal,
                        reference_rng,
                    )
                    candidate_sigma_pinv = sigma_theta_pinv_from_single(candidate_sigma_single, shots_per_epoch)
                    candidate_threshold = own_null_threshold(
                        candidate_circuit,
                        indices,
                        candidate_theta,
                        N=shots_per_epoch,
                        B=recalibration_B,
                        rng=reference_rng,
                        sigma_single=candidate_sigma_single,
                    )
                    candidate_reference_cache[candidate_p] = (
                        candidate_circuit,
                        current_matching,
                        np.asarray(candidate_theta, dtype=float),
                        candidate_sigma_pinv,
                        candidate_threshold,
                    )
                _candidate_circuit, current_matching, current_theta_model, current_sigma_pinv, current_threshold = candidate_reference_cache[candidate_p]
            recalibration_events += 1
            recalibration_epochs.append(epoch)
            candidate_ps.append(candidate_p)
            if first_recalibration_epoch is None:
                first_recalibration_epoch = epoch

        static_rates.append(float(np.mean(logical_error_bits(matching_static, dets_pm1, obs_bits))))
        oracle_matching = matching_static if epoch < drift_epoch else matching_oracle
        oracle_rates.append(float(np.mean(logical_error_bits(oracle_matching, dets_pm1, obs_bits))))
        if policy == "static":
            policy_matching = matching_static
        elif policy == "oracle":
            policy_matching = oracle_matching
        else:
            policy_matching = current_matching
        policy_rates.append(float(np.mean(logical_error_bits(policy_matching, dets_pm1, obs_bits))))
        witness_stats.append(stat)

    return {
        "policy": policy,
        "schedule_K": schedule_K,
        "policy_error_rates": policy_rates,
        "static_error_rates": static_rates,
        "oracle_error_rates": oracle_rates,
        "recalibration_events": recalibration_events,
        "first_recalibration_epoch": first_recalibration_epoch,
        "recalibration_epochs": recalibration_epochs,
        "candidate_ps": candidate_ps,
        "witness_stats": witness_stats,
    }


def _epoch_witness_stat(
    dets_pm1: np.ndarray,
    indices: list[tuple[int, ...]],
    theta_model: np.ndarray,
    sigma_theta_pinv: np.ndarray,
) -> float:
    theta_hat = _epoch_theta_hat(dets_pm1, indices)
    return w2_prime_statistic(theta_hat, theta_model, sigma_theta_pinv)


def _epoch_theta_hat(dets_pm1: np.ndarray, indices: list[tuple[int, ...]]) -> np.ndarray:
    return np.asarray(degree2_features(dets_pm1, indices), dtype=float).mean(axis=0)


def _recalibrated_candidate(dets_pm1: np.ndarray, curve: list[tuple[float, float]]) -> float:
    mean_flip = float((np.asarray(dets_pm1) == -1).mean())
    return nearest_candidate(mean_flip, curve)


def _recalibrated_circuit(distance: int | None, rounds: int | None, p0, candidate_p: float) -> stim.Circuit:
    if distance is None or rounds is None or p0 is None:
        raise ValueError("distance, rounds, and p0 are required for recalibrating policies")
    return build_memory_circuit_asymmetric(distance, rounds, p0, p0, candidate_p, p0)
