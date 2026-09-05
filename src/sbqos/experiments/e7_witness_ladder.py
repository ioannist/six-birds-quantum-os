"""E7 corrected syndrome-only witness ladder experiment runner."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from math import isfinite

import numpy as np

from sbqos import rng as project_rng
from sbqos.artifacts import Run, parse_fraction
from sbqos.codes import Code, surface_code
from sbqos.experiments.common import main_template, setup_matplotlib

setup_matplotlib()

from sbqos.experiments.e2_drift_witness import (
    _MatchingAdapter,
    _baseline_detector,
    _baseline_truth_result,
    _det_ratio_ok,
    _n_det,
    _naming_overlap,
    _unit,
)
from sbqos.moments import MomentEngine, ProbeFamily, degree2_family
from sbqos.noise import n2, n3
from sbqos.streams import (
    cusum_detect,
    cusum_null_threshold,
    degree2_model_params,
    omega_stat,
    qubit_logical_sensitivity,
    qubit_rate_dictionary,
    sample_shots,
    w1_witness,
    w2_witness,
    w2b_statistic,
    w2c_naming,
    w2d_shot_scores,
)
from sbqos.w2_diagnosis import bernoulli_kl, full_syndrome_pmf, own_null_scale, signal_budget, syndrome_kl
from sbqos.xi import blind_spot_witness, xi_residual

import matplotlib.pyplot as plt


def main(config_path: str) -> None:
    main_template(config_path, _run)


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    code = surface_code(3)
    L = ProbeFamily("native", code.checks, tuple(f"h{i}" for i in range(len(code.checks))))
    D = ProbeFamily("logical", code.logicals, ("Xbar", "Zbar"))
    F = degree2_family(L)
    p = parse_fraction(config["surf3_p"])
    q = parse_fraction(config["inject_q"])
    declared = n2(p, code.n)
    pairs = tuple(tuple(int(x) for x in pair) for pair in config["inject_pairs"])
    n_grid = tuple(int(x) for x in config["n_grid"])
    n_seeds = int(config["n_seeds"])
    bootstrap_B = int(config["bootstrap_B"])
    detect_required = int(config["detect_seeds_required"])
    naming_step = parse_fraction(config["naming_step"])

    exact_engine = MomentEngine(declared, exact=True)
    model_blocks = exact_engine.cov_blocks(L, D)
    _Xi, A_star = xi_residual(model_blocks)
    model_blocks_float = MomentEngine(declared, exact=False).cov_blocks(L, D)
    theta_by_N = {N: degree2_model_params(exact_engine, F, N) for N in set(n_grid) | {1, 4000}}
    theta_model = theta_by_N[1][0]
    sigma_single_pinv = np.linalg.pinv(np.asarray(theta_by_N[1][1], dtype=float), rcond=1e-12)
    dictionary = qubit_rate_dictionary(declared, F, step=naming_step)
    logical_sensitivity = {q_idx: qubit_logical_sensitivity(declared, q_idx, L, D, step=naming_step) for q_idx in range(code.n)}
    declared_pmf = full_syndrome_pmf(exact_engine, L)
    baseline = _baseline_detector(code, declared, L, D, int(config["baseline_model_shots"]), seed + 70_000_000)
    w2d_baseline, w2d_threshold = cusum_null_threshold(
        code,
        declared,
        L,
        D,
        F,
        theta_model,
        sigma_single_pinv,
        int(config["cusum_run_length"]),
        int(config["cusum_B"]),
        project_rng(seed + 71_000_000),
        float(config["cusum_target_false_alarm"]),
    )
    baseline_cusum_baseline, baseline_cusum_threshold = _baseline_cusum_threshold(
        code,
        declared,
        L,
        D,
        int(config["cusum_run_length"]),
        int(config["cusum_B"]),
        project_rng(seed + 72_000_000),
        float(config["cusum_target_false_alarm"]),
    )
    w2a_thresholds, w2b_thresholds = _thresholds_by_N(
        code,
        declared,
        L,
        D,
        F,
        A_star,
        n_grid,
        theta_by_N,
        bootstrap_B,
        seed + 73_500_000,
    )
    p71 = _p71_threshold_comparison(code, declared, L, D, model_blocks_float, A_star, N=4000, B=bootstrap_B, seed=seed + 73_000_000)

    scenarios = []
    for scenario_index, pair in enumerate(pairs):
        truth = n3(p, q, code.n, pair)
        scenarios.append(
            _scenario_run(
                code=code,
                declared=declared,
                truth=truth,
                pair=pair,
                scenario_index=scenario_index,
                L=L,
                D=D,
                F=F,
                model_blocks=model_blocks,
                model_blocks_float=model_blocks_float,
                A_star=A_star,
                theta_by_N=theta_by_N,
                w2a_thresholds=w2a_thresholds,
                w2b_thresholds=w2b_thresholds,
                theta_model=theta_model,
                sigma_single_pinv=sigma_single_pinv,
                dictionary=dictionary,
                logical_sensitivity=logical_sensitivity,
                declared_pmf=declared_pmf,
                baseline=baseline,
                w2d_baseline=w2d_baseline,
                w2d_threshold=w2d_threshold,
                baseline_cusum_baseline=baseline_cusum_baseline,
                baseline_cusum_threshold=baseline_cusum_threshold,
                n_grid=n_grid,
                n_seeds=n_seeds,
                bootstrap_B=bootstrap_B,
                detect_required=detect_required,
                baseline_model_shots=int(config["baseline_model_shots"]),
                seed=seed,
            )
        )

    null = _null_calibration(
        code,
        declared,
        L,
        D,
        F,
        model_blocks_float,
        A_star,
        theta_by_N[4000],
        w2a_thresholds[4000],
        w2b_thresholds[4000],
        theta_model,
        sigma_single_pinv,
        w2d_baseline,
        w2d_threshold,
        baseline,
        baseline_cusum_baseline,
        baseline_cusum_threshold,
        N=4000,
        cusum_run_length=int(config["cusum_run_length"]),
        B=bootstrap_B,
        runs=int(config["null_runs"]),
        seed=seed + 80_000_000,
    )
    predictions = _predictions(scenarios, p71, null)
    results = {
        "experiment": "e7",
        "claim_grade": "measured",
        "config_summary": {
            "n_grid": list(n_grid),
            "n_seeds": n_seeds,
            "detect_seeds_required": detect_required,
            "bootstrap_B": bootstrap_B,
            "cusum": {
                "w2d_baseline": w2d_baseline,
                "w2d_threshold": w2d_threshold,
                "baseline_cusum_baseline": baseline_cusum_baseline,
                "baseline_cusum_threshold": baseline_cusum_threshold,
            },
        },
        "p71_threshold_comparison": p71,
        "scenarios": scenarios,
        "null_calibration": null,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_detection_figure(run, scenarios)
    _save_naming_figure(run, scenarios)


def _scenario_run(**kwargs) -> dict:
    code: Code = kwargs["code"]
    declared = kwargs["declared"]
    truth = kwargs["truth"]
    pair = kwargs["pair"]
    scenario_index = kwargs["scenario_index"]
    L: ProbeFamily = kwargs["L"]
    D: ProbeFamily = kwargs["D"]
    F: ProbeFamily = kwargs["F"]
    model_blocks = kwargs["model_blocks"]
    model_blocks_float = kwargs["model_blocks_float"]
    A_star = kwargs["A_star"]
    theta_by_N = kwargs["theta_by_N"]
    w2a_thresholds = kwargs["w2a_thresholds"]
    w2b_thresholds = kwargs["w2b_thresholds"]
    theta_model = kwargs["theta_model"]
    sigma_single_pinv = kwargs["sigma_single_pinv"]
    dictionary = kwargs["dictionary"]
    logical_sensitivity = kwargs["logical_sensitivity"]
    declared_pmf = kwargs["declared_pmf"]
    baseline = kwargs["baseline"]
    n_grid = kwargs["n_grid"]
    n_seeds = kwargs["n_seeds"]
    bootstrap_B = kwargs["bootstrap_B"]
    detect_required = kwargs["detect_required"]
    seed = kwargs["seed"]

    counts = {method: {N: 0 for N in n_grid} for method in ("w2a", "w2b", "w2c", "w2d", "baseline", "baseline_cusum")}
    rows = []
    for n_index, N in enumerate(n_grid):
        theta_N, sigma_N = theta_by_N[N]
        for cell_seed in range(n_seeds):
            base_seed = seed + 1_000_000 * scenario_index + 1000 * n_index + cell_seed
            omega_a = w2a_thresholds[N]
            threshold_b = w2b_thresholds[N]
            shots_L = sample_shots(code, truth, L, D, N=N, rng=project_rng(base_seed + 400_000))
            shots_F = sample_shots(code, truth, F, D, N=N, rng=project_rng(base_seed + 500_000))
            w2a_value = w2_witness(shots_L, model_blocks_float, A_star, np.zeros((len(D.vecs), len(D.vecs)))).lam_max
            w2b_value = w2b_statistic(shots_F, F, theta_N, sigma_N)
            w2d_scores = w2d_shot_scores(shots_F, F, theta_model, kwargs["sigma_single_pinv"])
            baseline_result = _baseline_truth_result(baseline, shots_L)
            baseline_bits = _logical_error_bits(baseline["adapter"], shots_L).astype(float)

            detections = {
                "w2a": w2a_value > omega_a,
                "w2b": w2b_value > threshold_b,
                "w2c": w2b_value > threshold_b,
                "w2d": cusum_detect(w2d_scores, kwargs["w2d_baseline"], kwargs["w2d_threshold"]) is not None,
                "baseline": bool(baseline_result["detected"]),
                "baseline_cusum": cusum_detect(baseline_bits, kwargs["baseline_cusum_baseline"], kwargs["baseline_cusum_threshold"]) is not None,
            }
            for method, detected in detections.items():
                counts[method][N] += int(detected)
            rows.append(
                {
                    "N": int(N),
                    "seed": int(cell_seed),
                    "w2a_value": float(w2a_value),
                    "w2a_threshold": float(omega_a),
                    "w2a_detected": detections["w2a"],
                    "w2b_value": float(w2b_value),
                    "w2b_threshold": float(threshold_b),
                    "w2b_detected": detections["w2b"],
                    "w2c_detected": detections["w2c"],
                    "w2d_detected": detections["w2d"],
                    "baseline_detected": detections["baseline"],
                    "baseline_cusum_detected": detections["baseline_cusum"],
                    "baseline_error_count": baseline_result["error_count"],
                    "baseline_pvalue": baseline_result["pvalue"],
                    "truth_F_seed": base_seed + 500_000,
                }
            )

    n_det = {method: _n_det(counts[method], n_grid, detect_required) for method in counts}
    analytic = _analytic_reference(declared, truth, L, D, declared_pmf, baseline, kwargs["baseline_model_shots"], seed, scenario_index, pair)
    naming = _naming_summary(
        code,
        truth,
        pair,
        F,
        D,
        n_det["w2b"],
        n_seeds,
        detect_required,
        seed,
        scenario_index,
        theta_by_N,
        dictionary,
        logical_sensitivity,
        analytic,
        rows,
    )
    fractions = [
        {
            "scenario": _pair_label(pair),
            "N": int(N),
            **{f"{method}_fraction": counts[method][N] / n_seeds for method in counts},
        }
        for N in n_grid
    ]
    return {
        "pair": list(pair),
        "pair_label": _pair_label(pair),
        "analytic": analytic,
        "rows": rows,
        "detection_counts": {method: {str(N): counts[method][N] for N in n_grid} for method in counts},
        "detection_fractions": fractions,
        "N_det": {method: (None if value is None else int(value)) for method, value in n_det.items()},
        "naming": naming,
    }


def _analytic_reference(declared, truth, L, D, declared_pmf, baseline, shots: int, seed: int, scenario_index: int, pair: tuple[int, int]) -> dict:
    Xi_declared, _ = xi_residual(MomentEngine(declared, exact=True).cov_blocks(L, D))
    Xi_truth, _ = xi_residual(MomentEngine(truth, exact=True).cov_blocks(L, D))
    w1 = blind_spot_witness(Xi_truth, Xi_declared, D.labels)
    truth_pmf = full_syndrome_pmf(MomentEngine(truth, exact=True), L)
    truth_shots = sample_shots(surface_code(3), truth, L, D, N=shots, rng=project_rng(seed + 90_000_000 + scenario_index))
    truth_error_count = baseline["adapter"].logical_errors(truth_shots)["error_count"]
    p0 = baseline["summary"]["p0"]
    p1 = truth_error_count / shots
    return {
        "w1_direction": [float(x) for x in _unit(w1.z)],
        "signal_budget": _signal_budget_record(signal_budget(declared, truth, L, D)),
        "syndrome_kl": syndrome_kl(declared_pmf, truth_pmf),
        "logical_failure_rate": p1,
        "logical_failure_count": truth_error_count,
        "declared_logical_failure_rate": p0,
        "logical_failure_bernoulli_kl": bernoulli_kl(p1, p0),
        "finding4_relation": _relation_label(pair),
    }


def _naming_summary(code, truth, pair, F, D, N_det, n_seeds, detect_required, seed, scenario_index, theta_by_N, dictionary, logical_sensitivity, analytic, rows) -> dict:
    if N_det is None:
        return {"defined": False, "reason": "W2b did not detect within grid"}
    theta_N, sigma_N = theta_by_N[N_det]
    named = []
    overlaps = []
    in_pair = 0
    del seed, scenario_index, n_seeds
    for row in rows:
        if row["N"] != N_det or not row["w2b_detected"]:
            continue
        cell_seed = int(row["seed"])
        shots = sample_shots(code, truth, F, D, N=N_det, rng=project_rng(int(row["truth_F_seed"])))
        value = w2b_statistic(shots, F, theta_N, sigma_N)
        if value <= row["w2b_threshold"]:
            continue
        theta_hat = np.asarray(shots.L_outcomes, dtype=float).mean(axis=0)
        sigma_pinv = np.linalg.pinv(np.asarray(sigma_N, dtype=float), rcond=1e-12)
        qubit, score = w2c_naming(theta_hat, theta_N, sigma_pinv, dictionary)
        overlap = _naming_overlap(logical_sensitivity[qubit], np.asarray(analytic["w1_direction"], dtype=float))
        named.append({"seed": cell_seed, "qubit": qubit, "score": score, "overlap": overlap, "in_pair": qubit in pair})
        overlaps.append(overlap)
        in_pair += int(qubit in pair)
    modal = Counter(row["qubit"] for row in named).most_common(1)
    return {
        "defined": True,
        "N": int(N_det),
        "detecting_seed_count": len(named),
        "required": detect_required,
        "named_in_pair_count": in_pair,
        "modal_qubit": None if not modal else int(modal[0][0]),
        "mean_overlap": None if not overlaps else float(np.mean(np.asarray(overlaps, dtype=float))),
        "rows": named,
    }


def _thresholds_by_N(code, declared, L, D, F, A_star, n_grid, theta_by_N, B, seed) -> tuple[dict[int, float], dict[int, float]]:
    w2a = {}
    w2b = {}
    for idx, N in enumerate(sorted(set(n_grid) | {4000})):
        theta_N, sigma_N = theta_by_N[N]
        w2a[N] = own_null_scale(
            code,
            declared,
            L,
            D,
            N,
            B,
            project_rng(seed + 10_000 * idx),
            lambda shots, blocks: w2_witness(shots, blocks, A_star, np.zeros((len(D.vecs), len(D.vecs)))).lam_max,
        )
        w2b[N] = own_null_scale(
            code,
            declared,
            F,
            D,
            N,
            B,
            project_rng(seed + 10_000 * idx + 5000),
            lambda shots, _blocks: w2b_statistic(shots, F, theta_N, sigma_N),
        )
    return w2a, w2b


def _null_calibration(
    code,
    declared,
    L,
    D,
    F,
    model_blocks_float,
    A_star,
    theta_sigma_4000,
    threshold_a,
    threshold_b,
    theta_model,
    sigma_single_pinv,
    w2d_baseline,
    w2d_threshold,
    baseline,
    baseline_cusum_baseline,
    baseline_cusum_threshold,
    N,
    cusum_run_length,
    B,
    runs,
    seed,
) -> dict:
    theta_N, sigma_N = theta_sigma_4000
    del B, theta_N, sigma_N
    counts = {"w2a": 0, "w2b": 0, "w2d": 0, "baseline": 0, "baseline_cusum": 0}
    rows = []
    for run_idx in range(runs):
        base_seed = seed + run_idx
        shots_L = sample_shots(code, declared, L, D, N=N, rng=project_rng(base_seed + 200_000))
        shots_F = sample_shots(code, declared, F, D, N=N, rng=project_rng(base_seed + 300_000))
        value_a = w2_witness(shots_L, model_blocks_float, A_star, np.zeros((len(D.vecs), len(D.vecs)))).lam_max
        value_b = w2b_statistic(shots_F, F, theta_sigma_4000[0], theta_sigma_4000[1])
        baseline_result = _baseline_truth_result(baseline, shots_L)
        cusum_shots_F = sample_shots(code, declared, F, D, N=cusum_run_length, rng=project_rng(base_seed + 400_000))
        cusum_scores = w2d_shot_scores(cusum_shots_F, F, theta_model, sigma_single_pinv)
        cusum_shots_L = sample_shots(code, declared, L, D, N=cusum_run_length, rng=project_rng(base_seed + 500_000))
        baseline_bits = _logical_error_bits(baseline["adapter"], cusum_shots_L).astype(float)
        detected = {
            "w2a": value_a > threshold_a,
            "w2b": value_b > threshold_b,
            "w2d": cusum_detect(cusum_scores, w2d_baseline, w2d_threshold) is not None,
            "baseline": bool(baseline_result["detected"]),
            "baseline_cusum": cusum_detect(baseline_bits, baseline_cusum_baseline, baseline_cusum_threshold) is not None,
        }
        for key, value in detected.items():
            counts[key] += int(value)
        rows.append({"run": run_idx, **{f"{key}_false_positive": value for key, value in detected.items()}})
    return {
        "N": N,
        "runs": runs,
        "rows": rows,
        "false_positive_rates": {key: (counts[key] / runs if runs else 0.0) for key in counts},
    }


def _p71_threshold_comparison(code, declared, L, D, model_blocks_float, A_star, N: int, B: int, seed: int) -> dict:
    values_a = []
    values_w1 = []
    Xi_model, _ = xi_residual(model_blocks_float)
    for b in range(B):
        shots = sample_shots(code, declared, L, D, N=N, rng=project_rng(seed + b))
        values_a.append(w2_witness(shots, model_blocks_float, A_star, np.zeros((len(D.vecs), len(D.vecs)))).lam_max)
        values_w1.append(w1_witness(shots, model_blocks_float, np.zeros((len(D.vecs), len(D.vecs)))).lam_max)
    del Xi_model
    w2a = float(np.percentile(np.asarray(values_a, dtype=float), 99.0))
    borrowed = float(np.percentile(np.asarray(values_w1, dtype=float), 99.0))
    return {"N": N, "B": B, "w2a_threshold": w2a, "borrowed_w1_threshold": borrowed, "ratio": (w2a / borrowed if borrowed else None)}


def _baseline_cusum_threshold(code, model, L, D, run_length: int, B: int, rng, target_false_alarm: float) -> tuple[float, float]:
    adapter = _MatchingAdapter(code, model)
    rows = []
    for _ in range(B):
        shots = sample_shots(code, model, L, D, N=run_length, rng=rng)
        rows.append(_logical_error_bits(adapter, shots).astype(float))
    all_scores = np.concatenate(rows)
    baseline = float(np.mean(all_scores))
    max_g = np.asarray([_cusum_max(row, baseline) for row in rows], dtype=float)
    allowed = int(np.floor(target_false_alarm * B))
    threshold = float(np.sort(max_g)[B - allowed - 1]) if allowed < B else 0.0
    return baseline, threshold


def _logical_error_bits(adapter: _MatchingAdapter, shots) -> np.ndarray:
    syndrome_bits = (np.asarray(shots.L_outcomes, dtype=np.int8) == -1).astype(np.uint8)
    true_bits = (np.asarray(shots.D_outcomes, dtype=np.int8) == -1).astype(np.uint8)
    pred_zbar = adapter.x_error_matching.decode_batch(syndrome_bits[:, :4]).reshape((-1,))
    pred_xbar = adapter.z_error_matching.decode_batch(syndrome_bits[:, 4:]).reshape((-1,))
    predicted = np.column_stack([pred_xbar, pred_zbar]).astype(np.uint8)
    return np.any(predicted != true_bits, axis=1)


def _cusum_max(scores: np.ndarray, baseline: float) -> float:
    g = 0.0
    max_g = 0.0
    for score in np.asarray(scores, dtype=float):
        g = max(0.0, g + float(score) - baseline)
        max_g = max(max_g, g)
    return max_g


def _predictions(scenarios: list[dict], p71: dict, null: dict) -> list[dict]:
    by_pair = {tuple(row["pair"]): row for row in scenarios}
    off = by_pair[(4, 8)]
    frozen = by_pair[(0, 3)]
    near = by_pair[(2, 5)]
    p71_ok = p71["ratio"] is not None and p71["ratio"] <= 0.10
    off_best = _best_det(off["N_det"], ("w2b", "w2c", "w2d"))
    p72_ok = _det_ratio_ok(off_best, off["N_det"]["baseline"], 10.0)
    p73_ok = _no_w2_beats_baseline(frozen["N_det"])
    naming = off["naming"]
    p75_ok = bool(naming.get("defined")) and naming["named_in_pair_count"] >= 8 and naming["mean_overlap"] is not None and naming["mean_overlap"] >= 0.6
    rates = null["false_positive_rates"]
    p76_ok = all(value <= 0.02 for value in rates.values())
    return [
        _prediction("P7.1", "W2a own-null threshold is at most 10 percent of borrowed W1 threshold", p71_ok, p71),
        _prediction("P7.2", "off-support best corrected W2 rung detects at least 10x earlier than baseline", p72_ok, {"pair": off["pair"], "best_w2_det": off_best, "baseline_det": off["N_det"]["baseline"], "all_N_det": off["N_det"]}),
        _prediction(
            "P7.3",
            "on original E2 scenario every W2 rung has N_det/baseline >= 1",
            p73_ok,
            {"pair": frozen["pair"], "N_det": frozen["N_det"]},
            interpretation="This registered expected-negative tests the Finding-4 KL ratio 0.665: the original E2 scenario is structurally hard for syndrome-only witnesses.",
        ),
        {"id": "P7.4", "statement": "near-parity scenario ratios are descriptive only", "verdict": "measured", "grade": "measured", "values": {"pair": near["pair"], "N_det": near["N_det"], "ratios": _ratios(near["N_det"])}, "interpretation": "No numeric bar was registered for pair (2,5)."},
        _prediction("P7.5", "off-support W2c naming names an injected qubit and maps to logical overlap >= 0.6", p75_ok, naming),
        _prediction("P7.6", "null false-positive rate is at most 2 percent for every tested rung", p76_ok, null["false_positive_rates"]),
        {"id": "P7.7", "statement": "sequential and fixed-window N_det values are reported symmetrically", "verdict": "measured", "grade": "measured", "values": {row["pair_label"]: {"w2d": row["N_det"]["w2d"], "baseline_cusum": row["N_det"]["baseline_cusum"], "baseline_fixed": row["N_det"]["baseline"]} for row in scenarios}, "interpretation": "No pass/fail bar was registered for P7.7."},
    ]


def _prediction(pid: str, statement: str, ok: bool, values, interpretation: str | None = None) -> dict:
    verdict = "registered-positive" if ok else "registered-negative"
    row = {"id": pid, "statement": statement, "verdict": verdict, "grade": verdict, "values": values}
    if interpretation is not None:
        row["interpretation"] = interpretation
    return row


def _best_det(n_det: dict, keys: tuple[str, ...]) -> int | None:
    vals = [n_det[key] for key in keys if n_det[key] is not None]
    return min(vals) if vals else None


def _no_w2_beats_baseline(n_det: dict) -> bool:
    baseline = n_det["baseline"]
    for key in ("w2a", "w2b", "w2c", "w2d"):
        value = n_det[key]
        if value is None:
            continue
        if baseline is None or value < baseline:
            return False
    return True


def _ratios(n_det: dict) -> dict:
    baseline = n_det["baseline"]
    return {key: (None if value is None or baseline in {None, 0} else value / baseline) for key, value in n_det.items()}


def _signal_budget_record(budget: dict) -> dict:
    return {
        "delta_mean_L": [str(x) for x in budget["delta_mean_L"]],
        "delta_mean_L_norm_sq": budget["delta_mean_L_norm_sq"],
        "delta_K_LL_frobenius_sq": budget["delta_K_LL_frobenius_sq"],
        "delta_D_lifted_frobenius_sq": budget["delta_D_lifted_frobenius_sq"],
    }


def _pair_label(pair: tuple[int, int]) -> str:
    return f"{pair[0]}_{pair[1]}"


def _relation_label(pair: tuple[int, int]) -> str:
    if pair == (0, 3):
        return "two_qubits_on_Zbar"
    if pair == (2, 5):
        return "near_parity"
    if pair == (4, 8):
        return "off_support"
    return "unspecified"


def _save_detection_figure(run: Run, scenarios: list[dict]) -> None:
    rows = []
    fig, ax = plt.subplots(figsize=(7, 4))
    for scenario in scenarios:
        xs = [row["N"] for row in scenario["detection_fractions"]]
        ys = [row["w2b_fraction"] for row in scenario["detection_fractions"]]
        ax.plot(xs, ys, marker="o", label=f"{scenario['pair_label']} W2b")
        for row in scenario["detection_fractions"]:
            rows.append([scenario["pair_label"], row["N"], row["w2a_fraction"], row["w2b_fraction"], row["w2d_fraction"], row["baseline_fraction"], row["baseline_cusum_fraction"]])
    ax.set_xscale("log")
    ax.set_xlabel("shots")
    ax.set_ylabel("detection fraction")
    ax.legend(fontsize=7)
    ax.set_title("E7 corrected witness ladder")
    run.save_figure(fig, "e7_detection_latency", rows, ["scenario", "N", "w2a", "w2b", "w2d", "baseline", "baseline_cusum"])
    plt.close(fig)


def _save_naming_figure(run: Run, scenarios: list[dict]) -> None:
    rows = []
    labels = []
    values = []
    for scenario in scenarios:
        naming = scenario["naming"]
        if not naming.get("defined"):
            continue
        label = scenario["pair_label"]
        overlap = naming["mean_overlap"] if naming["mean_overlap"] is not None else 0.0
        rows.append([label, naming["modal_qubit"], naming["named_in_pair_count"], overlap])
        labels.append(label)
        values.append(overlap)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, values, color="black")
    ax.set_ylim(0, 1)
    ax.set_ylabel("mean overlap")
    ax.set_title("E7 W2c naming")
    run.save_figure(fig, "e7_naming_overlap", rows, ["scenario", "modal_qubit", "named_in_pair_count", "mean_overlap"])
    plt.close(fig)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e7_witness_ladder <config.json>")
    main(sys.argv[1])
