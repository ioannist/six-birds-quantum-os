"""E8 circuit-level global-drift witness runner."""

from __future__ import annotations

from fractions import Fraction

import numpy as np
from scipy.stats import binomtest

from sbqos import rng as project_rng
from sbqos.artifacts import Run, parse_fraction
from sbqos.circuit_level import (
    build_memory_circuit,
    degree2_detector_indices,
    degree2_features,
    detector_shots,
    estimate_model_params,
    logical_error_bits,
    own_null_threshold,
    pymatching_baseline,
    sigma_theta_pinv_from_single,
    w2_prime_statistic,
)
from sbqos.experiments.common import main_template, setup_matplotlib

setup_matplotlib()

import matplotlib.pyplot as plt


def main(config_path: str) -> None:
    main_template(config_path, _run)


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    distance = int(config["distance"])
    rounds = int(config["rounds"])
    p0 = parse_fraction(config["p0"])
    p1 = Fraction(int(config["p1_multiplier"])) * p0
    n_grid = tuple(int(x) for x in config["n_grid"])
    n_seeds = int(config["n_seeds"])
    required = int(config["detect_seeds_required"])
    bootstrap_B = int(config["bootstrap_B"])

    declared = build_memory_circuit(distance, rounds, p0)
    truth = build_memory_circuit(distance, rounds, p1)
    indices = degree2_detector_indices(declared.num_detectors)

    theta_model, sigma_single = estimate_model_params(
        declared,
        indices,
        int(config["N_cal"]),
        project_rng(seed + 8_000_000),
    )
    thresholds = _thresholds_by_N(declared, indices, theta_model, sigma_single, n_grid, bootstrap_B, seed + 8_100_000)
    matching = pymatching_baseline(declared)
    baseline = _baseline_calibration(
        declared,
        matching,
        int(config["baseline_calibration_shots"]),
        seed + 8_200_000,
    )

    sweep = _detection_sweep(
        truth,
        matching,
        indices,
        theta_model,
        sigma_single,
        thresholds,
        baseline["p0_logical_for_test"],
        n_grid,
        n_seeds,
        required,
        seed + 8_300_000,
    )
    null = _null_calibration(
        declared,
        matching,
        indices,
        theta_model,
        sigma_single,
        thresholds,
        baseline["p0_logical_for_test"],
        int(config["null_runs"]),
        bootstrap_B,
        seed + 8_400_000,
    )

    predictions = _predictions(sweep["N_det"], null["false_positive_rates"])
    results = {
        "config_summary": {
            "distance": distance,
            "rounds": rounds,
            "p0": str(p0),
            "p1": str(p1),
            "p1_multiplier": int(config["p1_multiplier"]),
        },
        "model_shape": {
            "num_detectors": declared.num_detectors,
            "num_observables": declared.num_observables,
            "degree2_feature_count": len(indices),
        },
        "calibration": {
            "N_cal": int(config["N_cal"]),
            "baseline_calibration_shots": int(config["baseline_calibration_shots"]),
            "p0_logical": baseline["p0_logical"],
            "baseline_error_count": baseline["error_count"],
            "thresholds": {str(N): thresholds[N] for N in n_grid},
        },
        "detection": sweep,
        "null_calibration": null,
        "cost_scaling": {
            "num_detectors": declared.num_detectors,
            "degree2_feature_count": len(indices),
            "distance5_status": "deferred_future_work",
            "wall_clock_seconds": None,
            "wall_clock_note": "omitted from results.json to preserve byte-identical deterministic artifacts; reported by the packet runner",
        },
        "predictions": predictions,
    }
    run.write_result(results)
    _save_detection_figure(run, sweep["fractions"])


def _thresholds_by_N(
    circuit,
    indices,
    theta_model,
    sigma_single,
    n_grid: tuple[int, ...],
    B: int,
    seed: int,
) -> dict[int, float]:
    return {
        N: own_null_threshold(
            circuit,
            indices,
            theta_model,
            N=N,
            B=B,
            rng=project_rng(seed + N),
            sigma_single=sigma_single,
        )
        for N in n_grid
    }


def _baseline_calibration(circuit, matching, shots: int, seed: int) -> dict:
    dets_pm1, obs_bits = detector_shots(circuit, shots, project_rng(seed))
    errors = logical_error_bits(matching, dets_pm1, obs_bits)
    error_count = int(np.count_nonzero(errors))
    p0 = float(error_count / shots)
    p0_for_test = p0 if p0 > 0.0 else 0.5 / shots
    return {
        "shots": shots,
        "error_count": error_count,
        "p0_logical": p0,
        "p0_logical_for_test": p0_for_test,
    }


def _detection_sweep(
    truth,
    matching,
    indices,
    theta_model,
    sigma_single,
    thresholds: dict[int, float],
    p0_logical: float,
    n_grid: tuple[int, ...],
    n_seeds: int,
    required: int,
    seed: int,
) -> dict:
    counts = {"witness": {N: 0 for N in n_grid}, "baseline": {N: 0 for N in n_grid}}
    rows = []
    for N in n_grid:
        sigma_pinv = sigma_theta_pinv_from_single(sigma_single, N)
        for seed_idx in range(n_seeds):
            cell_seed = seed + 10_000 * N + seed_idx
            dets_pm1, obs_bits = detector_shots(truth, N, project_rng(cell_seed))
            stat = _statistic_from_dets(dets_pm1, indices, theta_model, sigma_pinv)
            witness_detected = stat > thresholds[N]
            errors = logical_error_bits(matching, dets_pm1, obs_bits)
            error_count = int(np.count_nonzero(errors))
            pvalue = float(binomtest(error_count, N, p0_logical).pvalue)
            baseline_detected = pvalue < 0.01
            counts["witness"][N] += int(witness_detected)
            counts["baseline"][N] += int(baseline_detected)
            rows.append(
                {
                    "N": N,
                    "seed_index": seed_idx,
                    "witness_stat": stat,
                    "witness_threshold": thresholds[N],
                    "witness_detected": witness_detected,
                    "baseline_error_count": error_count,
                    "baseline_pvalue": pvalue,
                    "baseline_detected": baseline_detected,
                }
            )
    fractions = [
        {
            "N": N,
            "witness_fraction": counts["witness"][N] / n_seeds,
            "baseline_fraction": counts["baseline"][N] / n_seeds,
        }
        for N in n_grid
    ]
    return {
        "N_det": {
            "witness": _n_det(counts["witness"], n_grid, required),
            "baseline": _n_det(counts["baseline"], n_grid, required),
            "required": required,
        },
        "counts": {
            "witness": {str(N): counts["witness"][N] for N in n_grid},
            "baseline": {str(N): counts["baseline"][N] for N in n_grid},
        },
        "fractions": fractions,
        "rows": rows,
    }


def _null_calibration(
    declared,
    matching,
    indices,
    theta_model,
    sigma_single,
    thresholds: dict[int, float],
    p0_logical: float,
    runs: int,
    B: int,
    seed: int,
) -> dict:
    N = 500
    if N not in thresholds:
        threshold = own_null_threshold(
            declared,
            indices,
            theta_model,
            N=N,
            B=B,
            rng=project_rng(seed + 500_000),
            sigma_single=sigma_single,
        )
    else:
        threshold = thresholds[N]
    sigma_pinv = sigma_theta_pinv_from_single(sigma_single, N)
    witness_fp = 0
    baseline_fp = 0
    rows = []
    for run_idx in range(runs):
        dets_pm1, obs_bits = detector_shots(declared, N, project_rng(seed + run_idx))
        stat = _statistic_from_dets(dets_pm1, indices, theta_model, sigma_pinv)
        witness_detected = stat > threshold
        errors = logical_error_bits(matching, dets_pm1, obs_bits)
        error_count = int(np.count_nonzero(errors))
        pvalue = float(binomtest(error_count, N, p0_logical).pvalue)
        baseline_detected = pvalue < 0.01
        witness_fp += int(witness_detected)
        baseline_fp += int(baseline_detected)
        rows.append(
            {
                "run": run_idx,
                "N": N,
                "witness_stat": stat,
                "witness_threshold": threshold,
                "witness_false_positive": witness_detected,
                "baseline_error_count": error_count,
                "baseline_pvalue": pvalue,
                "baseline_false_positive": baseline_detected,
            }
        )
    return {
        "N": N,
        "runs": runs,
        "bootstrap_B": B,
        "false_positive_rates": {
            "witness": witness_fp / runs if runs else 0.0,
            "baseline": baseline_fp / runs if runs else 0.0,
        },
        "rows": rows,
    }


def _statistic_from_dets(dets_pm1, indices, theta_model, sigma_pinv) -> float:
    theta_hat = np.asarray(degree2_features(dets_pm1, indices), dtype=float).mean(axis=0)
    return w2_prime_statistic(theta_hat, theta_model, sigma_pinv)


def _n_det(counts: dict[int, int], n_grid: tuple[int, ...], required: int) -> int | None:
    for N in n_grid:
        if counts[N] >= required:
            return N
    return None


def _predictions(n_det: dict, fp_rates: dict) -> list[dict]:
    witness = n_det["witness"]
    baseline = n_det["baseline"]
    p81_ok = witness is not None and (baseline is None or float(witness) <= float(baseline) / 2.0)
    p82_ok = all(float(value) <= 0.02 for value in fp_rates.values())
    ratio = None if witness in {None, 0} or baseline is None else float(baseline) / float(witness)
    return [
        _prediction(
            "P8.1",
            "circuit-level W2' detects at least 2x earlier than the pymatching baseline",
            p81_ok,
            {"N_det_witness": witness, "N_det_baseline": baseline, "baseline_over_witness_ratio": ratio},
        ),
        _prediction(
            "P8.2",
            "null false-positive rate is <= 2% for witness and baseline",
            p82_ok,
            {"false_positive_rates": fp_rates},
        ),
        {
            "id": "P8.cost",
            "statement": "circuit-level cost/scaling quantities are reported descriptively",
            "verdict": "measured",
            "grade": "measured",
            "values": {"bar": None},
            "interpretation": "No pass/fail bar was frozen for the cost/scaling report.",
        },
    ]


def _prediction(pid: str, statement: str, ok: bool, values: dict) -> dict:
    verdict = "registered-positive" if ok else "registered-negative"
    return {"id": pid, "statement": statement, "verdict": verdict, "grade": verdict, "values": values}


def _save_detection_figure(run: Run, fractions: list[dict]) -> None:
    rows = [[row["N"], row["witness_fraction"], row["baseline_fraction"]] for row in fractions]
    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [row["N"] for row in fractions]
    ax.plot(xs, [row["witness_fraction"] for row in fractions], marker="o", label="W2'")
    ax.plot(xs, [row["baseline_fraction"] for row in fractions], marker="o", label="baseline")
    ax.set_xscale("log")
    ax.set_xlabel("shots")
    ax.set_ylabel("detection fraction")
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.set_title("E8 circuit-level drift detection")
    run.save_figure(fig, "e8_detection_latency", rows, ["N", "witness_frac", "baseline_frac"])
    plt.close(fig)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e8_circuit_level <config.json>")
    main(sys.argv[1])
