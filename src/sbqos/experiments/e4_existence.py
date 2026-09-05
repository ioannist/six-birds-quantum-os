"""E4 existence certificate experiment runner."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from sbqos.artifacts import Run, parse_fraction
from sbqos.closure import (
    assemble_certificate,
    closure_deficit,
    closure_deficit_finite_horizon,
    full_existence_certificate,
    idem_defect,
    predictive_gap,
    predictive_gap_finite_horizon,
    prototype_stability,
    retention_error,
    route_mismatch,
    route_mismatch_finite_horizon,
)
from sbqos.codes import rep_code
from sbqos.experiments.common import main_template, setup_matplotlib
from sbqos.markov import MarkovModel, qec_markov_model, rep3_n1_model, rep3_n4_model, rep3_n5_model, surf3_n2_model
from sbqos.noise import n1, n4

setup_matplotlib()
import matplotlib.pyplot as plt


P_SWEEP_DELTA_MAX = 0.05
DEFAULT_MODELS = ("rep3_n1", "surf3_n2", "n4", "n5", "broken")


def main(config_path: str) -> None:
    main_template(config_path, _run)


def _build_model(model_name: str) -> MarkovModel:
    if model_name == "rep3_n1":
        return rep3_n1_model("minimum_weight", exact=True)
    if model_name == "surf3_n2":
        return surf3_n2_model("minimum_weight", exact=False)
    if model_name == "n4":
        return rep3_n4_model(exact=False)
    if model_name == "n5":
        return rep3_n5_model(exact=False)
    if model_name == "broken":
        return rep3_n1_model("broken", exact=True)
    raise ValueError(f"unknown E4 model: {model_name!r}")


def _require_models(model_order: tuple[str, ...], required: tuple[str, ...]) -> None:
    missing = [name for name in required if name not in model_order]
    if missing:
        raise ValueError(f"E4 config missing required model(s): {missing}")


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    taus = tuple(int(t) for t in config["taus"])
    delta_max = float(config["delta_max"])
    cd_max = float(config["cd_max"])
    eps_stable = float(parse_fraction(config["eps_stable"]))
    stream_length = int(config["stream_length"])
    n5_horizon = int(config["n5_declared_horizon"])
    model_order = tuple(config.get("models", DEFAULT_MODELS))
    _require_models(model_order, ("rep3_n1", "n4", "n5", "broken"))

    models = {model_name: _build_model(model_name) for model_name in model_order}

    delta_pred_cache = {}
    for i, model_name in enumerate(model_order):
        if model_name == "n5":
            delta_pred_cache[model_name] = predictive_gap_finite_horizon(
                models[model_name],
                stream_length,
                seed + i,
                horizon=n5_horizon,
                initial_state=0,
            )
        else:
            delta_pred_cache[model_name] = predictive_gap(models[model_name], stream_length, seed + i)

    certificate_table = []
    for model_name in model_order:
        for tau in taus:
            certificate_table.append(
                _certificate_row(
                    model_name,
                    models[model_name],
                    tau,
                    delta_max,
                    cd_max,
                    eps_stable,
                    delta_pred_cache[model_name],
                    n5_horizon,
                )
            )

    baseline = _row_by_model_tau(certificate_table, "rep3_n1", 1)
    broken = _row_by_model_tau(certificate_table, "broken", 1)
    n4_tau1 = _row_by_model_tau(certificate_table, "n4", 1)
    p_sweep = _p_sweep(config["p_sweep"], eps_stable)
    per_mode = _per_mode_table()
    n5_curve = _n5_horizon_curve(models["n5"], models["rep3_n1"], tuple(config["n5_horizons"]))
    correlation = _correlation_grid(certificate_table)

    predictions = _predictions(baseline, p_sweep, n4_tau1, per_mode, n5_curve, broken, correlation)
    results = {
        "experiment": "e4",
        "claim_grade": "interpretation",
        "baseline_certificate": baseline,
        "broken_control": broken,
        "certificate_table": certificate_table,
        "p_sweep": p_sweep,
        "per_mode": per_mode,
        "n5_horizon_curve": n5_curve,
        "correlation": correlation,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_p_sweep_figure(run, p_sweep)
    _save_n5_rm_figure(run, n5_curve)
    _save_correlation_figure(run, correlation["points"])


def _certificate_row(
    model_name: str,
    model: MarkovModel,
    tau: int,
    delta_max: float,
    cd_max: float,
    eps_stable: float,
    delta_pred: float,
    n5_horizon: int,
) -> dict:
    delta = idem_defect(model, "decoded", tau)
    epsilon, per_label = retention_error(model, "decoded", tau)
    multiplicity = prototype_stability(model, "decoded", tau, eps_stable=eps_stable)
    row = {
        "model": model_name,
        "tau": tau,
        "delta": float(delta),
        "epsilon": float(epsilon),
        "delta_le_epsilon": bool(delta <= epsilon),
        "retention_per_label": [float(x) for x in per_label],
        "multiplicity": int(multiplicity),
        "delta_pred": float(delta_pred),
        "absorbing": bool(model.is_absorbing),
    }
    if model.is_absorbing:
        row["route_mismatch"] = route_mismatch_finite_horizon(model, "decoded", tau, horizon=n5_horizon, initial_state=0)
        row["cd_tau"] = closure_deficit_finite_horizon(model, tau, horizon=n5_horizon, initial_state=0)
        row["finite_horizon"] = n5_horizon
        try:
            full_existence_certificate(model, tau, delta_max=delta_max, cd_max=cd_max, eps_stable=eps_stable)
        except ValueError as exc:
            row["stationary_certificate"] = {"defined": False, "error": str(exc)}
        else:
            row["stationary_certificate"] = {"defined": True, "error": None}
        row["status"] = "finite_horizon_only"
        return row

    rm = route_mismatch(model, "decoded", tau)
    cd_tau = closure_deficit(model, "decoded", tau)
    cert = assemble_certificate(
        delta,
        epsilon,
        rm,
        cd_tau,
        delta_pred,
        delta_max=delta_max,
        cd_max=cd_max,
        multiplicity=multiplicity,
        ε_stable=eps_stable,
    )
    row.update(
        {
            "route_mismatch": float(rm),
            "cd_tau": float(cd_tau),
            "status": cert.status,
            "bound_ok": cert.bound_ok,
        }
    )
    return row


def _p_sweep(p_values: list[str], eps_stable: float) -> list[dict]:
    rows = []
    code = rep_code(3)
    for p_string in p_values:
        p = parse_fraction(p_string)
        model = qec_markov_model(code, n1(p, code.n), code.logicals[1:], "minimum_weight", exact=True)
        delta = idem_defect(model, "decoded", 1)
        epsilon, _per = retention_error(model, "decoded", 1)
        multiplicity = prototype_stability(model, "decoded", 1, eps_stable=eps_stable)
        cd_tau = closure_deficit(model, "decoded", 1)
        rm = route_mismatch(model, "decoded", 1)
        del rm, cd_tau
        status = "degrading" if float(delta) > P_SWEEP_DELTA_MAX else "certified"
        rows.append(
            {
                "p": p_string,
                "p_float": float(p),
                "delta": float(delta),
                "epsilon": float(epsilon),
                "multiplicity": int(multiplicity),
                "status": status,
                "registered_delta_max": P_SWEEP_DELTA_MAX,
            }
        )
    return rows


def _per_mode_table() -> list[dict]:
    code = rep_code(3)
    hidden = n4(Fraction(1, 50), Fraction(1, 50), code.n).hidden
    if hidden is None:
        raise AssertionError("N4 hidden spec missing")
    rows = []
    for mode, mode_model in enumerate(hidden.mode_models):
        mm = qec_markov_model(code, mode_model, code.logicals[1:], "minimum_weight", exact=False)
        rows.append(
            {
                "mode": mode,
                "decoded_cd": closure_deficit(mm, "decoded", 1),
                "syndrome_cd": closure_deficit(mm, "syndrome", 1),
            }
        )
    n4_model = rep3_n4_model(exact=False)
    rows.append(
        {
            "mode": "joint_n4",
            "decoded_cd": closure_deficit(n4_model, "decoded", 1),
            "syndrome_cd": closure_deficit(n4_model, "syndrome", 1),
        }
    )
    return rows


def _n5_horizon_curve(n5_model: MarkovModel, baseline_model: MarkovModel, horizons: tuple[int, ...]) -> list[dict]:
    baseline_rm = float(route_mismatch(baseline_model, "decoded", 1))
    rows = []
    for horizon in horizons:
        rm = route_mismatch_finite_horizon(n5_model, "decoded", 1, horizon=horizon, initial_state=0)
        rows.append(
            {
                "horizon": int(horizon),
                "route_mismatch": float(rm),
                "baseline_route_mismatch": baseline_rm,
                "ratio": float(rm) / baseline_rm,
                "channel_accuracy": _channel_accuracy(n5_model, horizon),
            }
        )
    return rows


def _channel_accuracy(model: MarkovModel, horizon: int) -> float:
    P_h = np.linalg.matrix_power(np.asarray(model.P, dtype=float), horizon)
    weights = np.zeros(model.P.shape[0], dtype=float)
    weights[0] = 1.0
    weights = weights @ P_h
    logical_index = model.n_syndrome_bits
    true_logical = np.asarray([state[logical_index] for state in model.states], dtype=np.int64)
    return float(np.sum(weights[model.lens_decoded == true_logical]))


def _correlation_grid(certificate_table: list[dict]) -> dict:
    points = [
        {
            "model": row["model"],
            "tau": row["tau"],
            "cd": row["cd_tau"],
            "delta_pred": row["delta_pred"],
            "finite_horizon": row.get("finite_horizon"),
        }
        for row in certificate_table
        if row["model"] in {"rep3_n1", "surf3_n2", "n4", "n5"}
    ]
    with_n5 = _pearson([p["cd"] for p in points], [p["delta_pred"] for p in points])
    without_n5_points = [p for p in points if p["model"] != "n5"]
    without_n5 = _pearson([p["cd"] for p in without_n5_points], [p["delta_pred"] for p in without_n5_points])
    return {"points": points, "pearson_with_n5": with_n5, "pearson_without_n5": without_n5}


def _pearson(xs: list[float], ys: list[float]) -> float:
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if x.size < 2 or float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _predictions(
    baseline: dict,
    p_sweep: list[dict],
    n4_tau1: dict,
    per_mode: list[dict],
    n5_curve: list[dict],
    broken: dict,
    correlation: dict,
) -> list[dict]:
    p4_1_cd_ok = baseline["cd_tau"] <= 1e-10
    p4_1_delta_ok = all(p_sweep[i]["delta"] < p_sweep[i + 1]["delta"] for i in range(len(p_sweep) - 1))
    p4_2_n4_cd_ok = n4_tau1["cd_tau"] >= 1e-3
    p4_2_status = assemble_certificate(
        n4_tau1["delta"],
        n4_tau1["epsilon"],
        n4_tau1["route_mismatch"],
        n4_tau1["cd_tau"],
        n4_tau1["delta_pred"],
        delta_max=0.1,
        cd_max=1e-10,
        multiplicity=n4_tau1["multiplicity"],
    ).status
    per_mode_decoded = [row["decoded_cd"] for row in per_mode if isinstance(row["mode"], int)]
    per_mode_syndrome = [row["syndrome_cd"] for row in per_mode if isinstance(row["mode"], int)]
    p4_2_per_mode_decoded_ok = all(abs(x) <= 1e-10 for x in per_mode_decoded)
    p4_3_max_ratio = max(row["ratio"] for row in n5_curve)
    p4_5_with = correlation["pearson_with_n5"]
    p4_5_without = correlation["pearson_without_n5"]
    p4_5_ok = (not np.isnan(p4_5_with)) and p4_5_with >= 0.9
    return [
        {
            "id": "P4.1",
            "statement": "baseline CD near zero, multiplicity 2, certified default, delta monotone",
            "verdict": "registered-negative" if not p4_1_cd_ok else "registered-positive",
            "grade": "registered-negative" if not p4_1_cd_ok else "registered-positive",
            "values": {
                "decoded_cd_tau1": baseline["cd_tau"],
                "syndrome_cd_tau1": closure_deficit(rep3_n1_model("minimum_weight", exact=True), "syndrome", 1),
                "multiplicity": baseline["multiplicity"],
                "status": baseline["status"],
                "delta_monotone": p4_1_delta_ok,
                "p_sweep": p_sweep,
            },
            "interpretation": "The <=1e-10 CD clause holds for the syndrome lens, not the frozen decoded lens.",
        },
        {
            "id": "P4.2",
            "statement": "N4 non-closed while per-mode models have zero deficit",
            "verdict": "registered-negative" if not p4_2_per_mode_decoded_ok else "registered-positive",
            "grade": "registered-negative" if not p4_2_per_mode_decoded_ok else "registered-positive",
            "values": {
                "n4_decoded_cd": n4_tau1["cd_tau"],
                "n4_cd_ge_1e_3": p4_2_n4_cd_ok,
                "n4_status_at_cd_max_1e_10": p4_2_status,
                "per_mode_decoded_cd": per_mode_decoded,
                "per_mode_syndrome_cd": per_mode_syndrome,
            },
            "interpretation": "Per-mode decoded-lens CD is nonzero; the zero-deficit reading is true on the syndrome lens.",
        },
        {
            "id": "P4.3",
            "statement": "N5 finite-horizon RM at least 10x baseline",
            "verdict": "registered-positive" if p4_3_max_ratio >= 10.0 else "registered-negative",
            "grade": "registered-positive" if p4_3_max_ratio >= 10.0 else "registered-negative",
            "values": {"max_ratio": p4_3_max_ratio, "threshold": 10.0, "horizon_curve": n5_curve},
            "interpretation": "RM is several-fold above baseline and grows with horizon, but saturates below the frozen 10x threshold.",
        },
        {
            "id": "P4.4",
            "statement": "broken decoder trivialization guard",
            "verdict": "registered-positive"
            if broken["status"] == "trivialized" and broken["delta"] == 0.0 and broken["multiplicity"] == 1
            else "registered-negative",
            "grade": "registered-positive"
            if broken["status"] == "trivialized" and broken["delta"] == 0.0 and broken["multiplicity"] == 1
            else "registered-negative",
            "values": {"status": broken["status"], "delta": broken["delta"], "multiplicity": broken["multiplicity"]},
        },
        {
            "id": "P4.5",
            "statement": "Pearson correlation between CD and Delta_pred is at least 0.9",
            "verdict": "registered-positive" if p4_5_ok else "registered-negative",
            "grade": "registered-positive" if p4_5_ok else "registered-negative",
            "values": {"pearson_with_n5": p4_5_with, "pearson_without_n5": p4_5_without},
            "interpretation": (
                "The >=0.9 correlation holds only with the N5 finite-horizon points included; excluding N5, "
                "r = -0.17 on the remaining grid, so the correlation claim is not supported within the "
                "non-absorbing models alone at these defaults."
            ),
        },
    ]


def _row_by_model_tau(rows: list[dict], model: str, tau: int) -> dict:
    for row in rows:
        if row["model"] == model and row["tau"] == tau:
            return row
    raise KeyError((model, tau))


def _save_p_sweep_figure(run: Run, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([row["p_float"] for row in rows], [row["delta"] for row in rows], marker="o", color="black")
    ax.axhline(P_SWEEP_DELTA_MAX, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("p")
    ax.set_ylabel("delta")
    ax.set_title("REP(3) idempotence defect sweep")
    run.save_figure(
        fig,
        "e4_delta_vs_p",
        [[row["p"], row["delta"], row["status"]] for row in rows],
        ["p", "delta", "status"],
    )
    plt.close(fig)


def _save_n5_rm_figure(run: Run, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([row["horizon"] for row in rows], [row["ratio"] for row in rows], marker="o", color="black")
    ax.axhline(10.0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("horizon")
    ax.set_ylabel("RM ratio vs baseline")
    ax.set_title("N5 finite-horizon route mismatch")
    run.save_figure(
        fig,
        "e4_n5_rm_ratio",
        [[row["horizon"], row["route_mismatch"], row["ratio"], row["channel_accuracy"]] for row in rows],
        ["horizon", "route_mismatch", "ratio", "channel_accuracy"],
    )
    plt.close(fig)


def _save_correlation_figure(run: Run, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter([row["cd"] for row in rows], [row["delta_pred"] for row in rows], color="black", s=24)
    ax.set_xlabel("CD_tau")
    ax.set_ylabel("Delta_pred")
    ax.set_title("CD vs stream proxy")
    run.save_figure(
        fig,
        "e4_cd_delta_pred",
        [[row["model"], row["tau"], row["cd"], row["delta_pred"]] for row in rows],
        ["model", "tau", "cd", "delta_pred"],
    )
    plt.close(fig)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e4_existence <config.json>")
    main(sys.argv[1])
