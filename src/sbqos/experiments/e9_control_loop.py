"""E9 closed-loop circuit-level control runner."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from sbqos import rng as project_rng
from sbqos.artifacts import Run, parse_fraction
from sbqos.circuit_level import (
    build_memory_circuit,
    build_memory_circuit_asymmetric,
    calibration_curve,
    degree2_detector_indices,
    estimate_model_params,
    own_null_threshold,
    pymatching_baseline,
    run_epoch_timeline,
    sigma_theta_pinv_from_single,
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
    measure_multiplier = int(config["measure_multiplier"])
    truth_measure_p = Fraction(measure_multiplier) * p0
    E_total = int(config["E_total"])
    drift_epoch = int(config["drift_epoch"])
    shots_per_epoch = int(config["shots_per_epoch"])
    N_cal = int(config["N_cal"])
    bootstrap_B = int(config["bootstrap_B"])

    declared = build_memory_circuit(distance, rounds, p0)
    truth = build_memory_circuit_asymmetric(distance, rounds, p0, p0, truth_measure_p, p0)
    indices = degree2_detector_indices(declared.num_detectors)
    theta_model, sigma_single = estimate_model_params(declared, indices, N_cal, project_rng(seed + 9_000_000))
    sigma_pinv = sigma_theta_pinv_from_single(sigma_single, shots_per_epoch)
    threshold = own_null_threshold(
        declared,
        indices,
        theta_model,
        N=shots_per_epoch,
        B=bootstrap_B,
        rng=project_rng(seed + 9_100_000),
        sigma_single=sigma_single,
    )
    curve = calibration_curve(
        distance,
        rounds,
        p0,
        list(config["candidate_multipliers"]),
        int(config["N_curve"]),
        project_rng(seed + 9_200_000),
    )
    matching_static = pymatching_baseline(declared)
    matching_oracle = pymatching_baseline(truth)

    reference_cache: dict = {}
    reference_rng = project_rng(seed + 9_500_000)
    policies = [
        _run_policy(
            "static",
            "static",
            None,
            0,
            config,
            declared,
            truth,
            matching_static,
            matching_oracle,
            indices,
            theta_model,
            sigma_pinv,
            threshold,
            curve,
            reference_cache,
            reference_rng,
        ),
        _run_policy(
            "oracle",
            "oracle",
            None,
            1,
            config,
            declared,
            truth,
            matching_static,
            matching_oracle,
            indices,
            theta_model,
            sigma_pinv,
            threshold,
            curve,
            reference_cache,
            reference_rng,
        ),
    ]
    witness = _run_policy(
        "witness",
        "witness",
        None,
        2,
        config,
        declared,
        truth,
        matching_static,
        matching_oracle,
        indices,
        theta_model,
        sigma_pinv,
        threshold,
        curve,
        reference_cache,
        reference_rng,
    )
    policies.append(witness)
    witness_budgets = [row["recalibration_events"] for row in witness["per_seed"]]
    policies.extend(
        [
            _run_policy(
                "scheduled_matched",
                "scheduled",
                None,
                3,
                config,
                declared,
                truth,
                matching_static,
                matching_oracle,
                indices,
                theta_model,
                sigma_pinv,
                threshold,
                curve,
                reference_cache,
                reference_rng,
                matched_budgets=witness_budgets,
            ),
            _run_policy(
                "scheduled_frequent",
                "scheduled",
                int(config["schedule_K_frequent"]),
                4,
                config,
                declared,
                truth,
                matching_static,
                matching_oracle,
                indices,
                theta_model,
                sigma_pinv,
                threshold,
                curve,
                reference_cache,
                reference_rng,
            ),
        ]
    )

    aggregate = {row["key"]: row["aggregate"] for row in policies}
    predictions = _predictions(aggregate)
    results = {
        "config_summary": {
            "distance": distance,
            "rounds": rounds,
            "p0": str(p0),
            "truth_before_measure_p": str(truth_measure_p),
            "measure_multiplier": measure_multiplier,
            "E_total": E_total,
            "drift_epoch": drift_epoch,
            "shots_per_epoch": shots_per_epoch,
        },
        "model_shape": {
            "num_detectors": declared.num_detectors,
            "num_observables": declared.num_observables,
            "degree2_feature_count": len(indices),
        },
        "calibration": {
            "N_cal": N_cal,
            "bootstrap_B": bootstrap_B,
            "threshold": threshold,
            "curve": [{"candidate_p": p, "mean_detector_flip": flip} for p, flip in curve],
            "witness_reference_cache_candidates": sorted(str(key) for key in reference_cache.keys()),
        },
        "policies": policies,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_policy_figure(run, policies)


def _run_policy(
    key: str,
    policy: str,
    schedule_K: int | None,
    policy_index: int,
    config: dict,
    declared,
    truth,
    matching_static,
    matching_oracle,
    indices,
    theta_model,
    sigma_pinv,
    threshold,
    curve,
    reference_cache: dict,
    reference_rng,
    matched_budgets: list[int] | None = None,
) -> dict:
    seed = int(config["seed"])
    E_total = int(config["E_total"])
    drift_epoch = int(config["drift_epoch"])
    shots_per_epoch = int(config["shots_per_epoch"])
    per_seed = []
    for seed_idx in range(int(config["n_seeds"])):
        timeline_rng = project_rng(seed + 1_000_000 * policy_index + seed_idx)
        fixed_epochs = None
        matched_budget = None
        if matched_budgets is not None:
            matched_budget = int(matched_budgets[seed_idx])
            if matched_budget > E_total:
                raise ValueError("matched schedule budget exceeds E_total")
            fixed_epochs = set(int(x) for x in timeline_rng.choice(E_total, size=matched_budget, replace=False))
        result = run_epoch_timeline(
            declared,
            truth,
            matching_static,
            matching_oracle,
            indices,
            theta_model,
            sigma_pinv,
            threshold,
            curve,
            E_total,
            drift_epoch,
            shots_per_epoch,
            policy,
            schedule_K,
            timeline_rng,
            distance=int(config["distance"]),
            rounds=int(config["rounds"]),
            p0=parse_fraction(config["p0"]),
            recalibration_N_cal=int(config["N_cal"]),
            recalibration_B=int(config["bootstrap_B"]),
            reference_cache=reference_cache if policy == "witness" else None,
            calibration_rng=reference_rng if policy == "witness" else None,
            fixed_recalibration_epochs=fixed_epochs,
        )
        epochs = result["recalibration_epochs"]
        per_seed.append(
            {
                "seed_index": seed_idx,
                "post_drift_mean_error": float(np.mean(result["policy_error_rates"][drift_epoch:])),
                "recalibration_events": result["recalibration_events"],
                "first_recalibration_epoch": result["first_recalibration_epoch"],
                "pre_drift_recalibration": any(epoch < drift_epoch for epoch in epochs),
                "recalibration_epochs": epochs,
                "matched_budget": matched_budget,
            }
        )
    aggregate = _aggregate_policy(per_seed)
    return {"key": key, "policy": policy, "schedule_K": schedule_K, "aggregate": aggregate, "per_seed": per_seed}


def _aggregate_policy(per_seed: list[dict]) -> dict:
    post = [row["post_drift_mean_error"] for row in per_seed]
    events = [row["recalibration_events"] for row in per_seed]
    pre = [row["pre_drift_recalibration"] for row in per_seed]
    return {
        "mean_post_drift_error": float(np.mean(post)),
        "mean_recalibration_events": float(np.mean(events)),
        "pre_drift_trigger_rate": float(np.mean(pre)),
        "event_counts": events,
    }


def _predictions(aggregate: dict) -> list[dict]:
    witness = aggregate["witness"]["mean_post_drift_error"]
    oracle = aggregate["oracle"]["mean_post_drift_error"]
    scheduled_matched = aggregate["scheduled_matched"]["mean_post_drift_error"]
    scheduled_frequent = aggregate["scheduled_frequent"]["mean_post_drift_error"]
    p91_ok = abs(witness - oracle) <= 0.01
    p92_ok = witness <= scheduled_matched
    return [
        _prediction(
            "P9.1",
            "witness-triggered control is within 0.01 of oracle post-drift error",
            p91_ok,
            {"witness": witness, "oracle": oracle, "absolute_gap": abs(witness - oracle)},
        ),
        _prediction(
            "P9.2",
            "witness-triggered control beats matched-budget scheduled recalibration",
            p92_ok,
            {
                "witness_error": witness,
                "scheduled_matched_error": scheduled_matched,
                "gap_scheduled_minus_witness": scheduled_matched - witness,
                "witness_mean_events": aggregate["witness"]["mean_recalibration_events"],
                "scheduled_matched_mean_events": aggregate["scheduled_matched"]["mean_recalibration_events"],
                "witness_event_counts": aggregate["witness"]["event_counts"],
                "scheduled_matched_event_counts": aggregate["scheduled_matched"]["event_counts"],
            },
        ),
        {
            "id": "P9.3",
            "statement": "higher-budget scheduled recalibration is reported descriptively",
            "verdict": "measured",
            "grade": "measured",
            "values": {
                "scheduled_frequent": scheduled_frequent,
                "witness": witness,
                "oracle": oracle,
                "scheduled_frequent_minus_witness": scheduled_frequent - witness,
                "scheduled_frequent_minus_oracle": scheduled_frequent - oracle,
            },
            "interpretation": "No pass/fail bar was frozen for the higher-budget schedule.",
        },
        {
            "id": "P9.4",
            "statement": "pre-drift recalibration rates are reported descriptively",
            "verdict": "measured",
            "grade": "measured",
            "values": {
                "witness": aggregate["witness"]["pre_drift_trigger_rate"],
                "scheduled_matched": aggregate["scheduled_matched"]["pre_drift_trigger_rate"],
                "scheduled_frequent": aggregate["scheduled_frequent"]["pre_drift_trigger_rate"],
            },
            "interpretation": "Scheduled pre-drift rates are scheduled recalibrations, not witness false alarms.",
        },
    ]


def _prediction(pid: str, statement: str, ok: bool, values: dict) -> dict:
    verdict = "registered-positive" if ok else "registered-negative"
    return {"id": pid, "statement": statement, "verdict": verdict, "grade": verdict, "values": values}


def _save_policy_figure(run: Run, policies: list[dict]) -> None:
    order = ["static", "oracle", "witness", "scheduled_matched", "scheduled_frequent"]
    by_key = {row["key"]: row for row in policies}
    rows = [[key, by_key[key]["aggregate"]["mean_post_drift_error"], by_key[key]["aggregate"]["mean_recalibration_events"]] for key in order]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([row[0] for row in rows], [row[1] for row in rows], color="black")
    ax.set_ylabel("post-drift logical error")
    ax.set_title("E9 closed-loop policy comparison")
    ax.tick_params(axis="x", rotation=20)
    run.save_figure(fig, "e9_post_drift_error", rows, ["policy", "mean_post_drift_error", "mean_recalibration_events"])
    plt.close(fig)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e9_control_loop <config.json>")
    main(sys.argv[1])
