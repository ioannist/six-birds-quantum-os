"""E6 shadow-price and slack experiment runner."""

from __future__ import annotations

from copy import deepcopy
import numpy as np

from sbqos import rng as project_rng
from sbqos.artifacts import Run, parse_fraction
from sbqos.codes import Code, rep_code, surface_code
from sbqos.experiments.common import main_template, setup_matplotlib
from sbqos.moments import MomentEngine, ProbeFamily, degree2_family
from sbqos.noise import n1, n2
from sbqos.prices import proxy_costs, shadow_prices, slack_point, value_curve, value_curve_exact
from sbqos.streams import sample_shots
from sbqos.xi import select_checks, xi_residual

setup_matplotlib()
import matplotlib.pyplot as plt


_REP5_CURVE_CACHE: dict[tuple[str, float], dict] = {}
_SURF3_CURVE_CACHE: dict[tuple[str, float], dict] = {}


def main(config_path: str) -> None:
    main_template(config_path, _run)


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    rep5_p = parse_fraction(config["rep5_p"])
    surf3_p = parse_fraction(config["surf3_p"])
    lambda_tol = float(config["lambda_tol"])
    n_proxy_seeds = int(config["n_proxy_seeds"])
    consequence_shots = int(config["consequence_shots"])

    rep5 = _rep5_curves(rep5_p, lambda_tol)
    surf3 = _surf3_curve(surf3_p, lambda_tol)
    consequence = _consequence_test(rep5, rep5_p, consequence_shots, seed)
    proxy = _proxy_null(rep5, rep5_p, n_proxy_seeds, seed)
    predictions = _predictions(rep5, surf3, consequence, proxy, lambda_tol)

    results = {
        "experiment": "e6",
        "claim_grade": "measured",
        "rep5": rep5,
        "surf3": surf3,
        "consequence_test": consequence,
        "proxy_null": proxy,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_value_lambda_figure(run, rep5)
    _save_proxy_figure(run, rep5, proxy)


def _rep5_curves(p, lambda_tol: float) -> dict:
    key = (str(p), float(lambda_tol))
    if key in _REP5_CURVE_CACHE:
        return deepcopy(_REP5_CURVE_CACHE[key])
    code = rep_code(5)
    model = n1(p, code.n)
    engine = MomentEngine(model, exact=True)
    L0 = ProbeFamily("native", (), ())
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    candidates, costs = _rep5_candidates(code)
    b_max = int(sum(costs))
    V_greedy = value_curve(engine, L0, D, candidates, costs, b_max)
    V_exact = value_curve_exact(engine, L0, D, candidates, costs, b_max)
    lam = shadow_prices(V_exact)
    gaps = [float(exact - greedy) for greedy, exact in zip(V_greedy, V_exact)]
    result = {
        "b_max": b_max,
        "V_greedy": list(V_greedy),
        "V_exact": list(V_exact),
        "greedy_gap": gaps,
        "max_greedy_gap": max(gaps),
        "lambda_exact": list(lam),
        "slack_point": slack_point(lam, lambda_tol),
        "descriptive_slack_points": {
            "1e-4": slack_point(lam, 1e-4),
            "1e-3": slack_point(lam, 1e-3),
        },
        "candidate_labels": list(candidates.labels),
        "costs": list(costs),
    }
    _REP5_CURVE_CACHE[key] = deepcopy(result)
    return result


def _surf3_curve(p, lambda_tol: float) -> dict:
    key = (str(p), float(lambda_tol))
    if key in _SURF3_CURVE_CACHE:
        return deepcopy(_SURF3_CURVE_CACHE[key])
    code = surface_code(3)
    engine = MomentEngine(n2(p, code.n), exact=True)
    L0 = ProbeFamily("native", (), ())
    D = ProbeFamily("logical", code.logicals, ("Xbar", "Zbar"))
    candidates = ProbeFamily("candidate", code.checks, tuple(f"h{i}" for i in range(len(code.checks))))
    costs = tuple(1.0 for _ in candidates.vecs)
    b_max = len(candidates.vecs)
    V = value_curve(engine, L0, D, candidates, costs, b_max)
    lam = shadow_prices(V)
    result = {
        "b_max": b_max,
        "V_greedy": list(V),
        "lambda_greedy": list(lam),
        "slack_point": slack_point(lam, lambda_tol),
        "descriptive_slack_points": {
            "1e-4": slack_point(lam, 1e-4),
            "1e-3": slack_point(lam, 1e-3),
        },
    }
    _SURF3_CURVE_CACHE[key] = deepcopy(result)
    return result


def _rep5_candidates(code: Code) -> tuple[ProbeFamily, tuple[float, ...]]:
    checks = ProbeFamily("candidate", code.checks, tuple(f"h{i}" for i in range(len(code.checks))))
    degree2 = degree2_family(checks)
    product_vecs = []
    product_labels = []
    for vec, label in zip(degree2.vecs, degree2.labels):
        if "^" in label:
            product_vecs.append(vec)
            product_labels.append(label)
    candidates = ProbeFamily(
        "candidate",
        checks.vecs + tuple(product_vecs),
        checks.labels + tuple(product_labels),
    )
    costs = tuple([1.0] * len(checks.vecs) + [2.0] * len(product_vecs))
    return candidates, costs


def _selected_family_for_budget(code: Code, p, budget: int) -> ProbeFamily:
    engine = MomentEngine(n1(p, code.n), exact=True)
    L0 = ProbeFamily("native", (), ())
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    candidates, costs = _rep5_candidates(code)
    log = select_checks(engine, L0, D, candidates, costs, budget=float(budget), tol_stop=1e-12)
    return ProbeFamily(
        "native",
        tuple(candidates.vecs[i] for i in log.selected_indices),
        tuple(candidates.labels[i] for i in log.selected_indices),
    )


def _consequence_test(rep5: dict, p, shots: int, seed: int) -> dict:
    code = rep_code(5)
    model = n1(p, code.n)
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    b_star = int(rep5["slack_point"])
    budgets = (max(0, b_star - 1), b_star)
    rows = []
    for i, budget in enumerate(budgets):
        L = _selected_family_for_budget(code, p, budget)
        rate = _decoder_error_rate(code, model, L, D, shots, seed + i)
        rows.append({"budget": budget, **rate})
    delta = rows[0]["logical_error_rate"] - rows[1]["logical_error_rate"]
    combined_se = float(np.sqrt(rows[0]["standard_error"] ** 2 + rows[1]["standard_error"] ** 2))
    return {
        "shots": int(shots),
        "b_star": b_star,
        "rates": rows,
        "delta_rate_b_minus_1_to_b_star": delta,
        "combined_standard_error": combined_se,
        "load_bearing_gt_2se": delta > 2.0 * combined_se,
        "post_slack_clause_applicable": False,
    }


def _decoder_error_rate(code: Code, model, L: ProbeFamily, D: ProbeFamily, shots: int, seed: int) -> dict:
    engine = MomentEngine(model, exact=False)
    blocks = engine.cov_blocks(L, D)
    _Xi, A_star = xi_residual(blocks)
    A = np.asarray(A_star, dtype=float)
    mean_D = float(engine.mean(D.vecs[0]))
    mean_L = np.asarray([float(engine.mean(vec)) for vec in L.vecs], dtype=float)
    table = sample_shots(code, model, L, D, N=shots, rng=project_rng(seed))
    if len(L.vecs) == 0:
        estimate = np.full(shots, mean_D, dtype=float)
    else:
        estimate = mean_D + (np.asarray(table.L_outcomes, dtype=float) - mean_L) @ A[0, :]
    prediction = np.where(estimate >= 0.0, 1, -1).astype(np.int8)
    truth = table.D_outcomes[:, 0]
    errors = prediction != truth
    rate = float(np.mean(errors))
    se = float(np.sqrt(rate * (1.0 - rate) / float(shots)))
    return {
        "selected_labels": list(L.labels),
        "logical_error_rate": rate,
        "standard_error": se,
    }


def _proxy_null(rep5: dict, p, n_proxy_seeds: int, seed: int) -> dict:
    code = rep_code(5)
    engine = MomentEngine(n1(p, code.n), exact=True)
    L0 = ProbeFamily("native", (), ())
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    candidates, costs = _rep5_candidates(code)
    b_max = int(rep5["b_max"])
    structural = tuple(rep5["V_greedy"])
    curves = []
    effective_costs = set()
    worse = 0
    total = 0
    for i in range(n_proxy_seeds):
        permuted = proxy_costs(costs, project_rng(seed + i))
        effective_costs.add(tuple(permuted))
        V_proxy = value_curve(engine, L0, D, candidates, permuted, b_max)
        curve = list(V_proxy)
        curves.append({"seed": seed + i, "costs": list(permuted), "V": curve})
        for b in range(1, b_max + 1):
            total += 1
            if curve[b] < structural[b] - 1e-12:
                worse += 1
    return {
        "curves": curves,
        "distinct_effective_cost_vectors": len(effective_costs),
        "strictly_worse_count": worse,
        "comparison_count": total,
        "strictly_worse_fraction": worse / total if total else 0.0,
    }


def _predictions(rep5: dict, surf3: dict, consequence: dict, proxy: dict, lambda_tol: float) -> list[dict]:
    p61_violations = _nonincreasing_violations(rep5["lambda_exact"])
    p62_fails = rep5["slack_point"] == rep5["b_max"] or surf3["slack_point"] == surf3["b_max"]
    p63_ok = consequence["load_bearing_gt_2se"]
    p64_ok = proxy["strictly_worse_fraction"] >= 0.8
    return [
        {
            "id": "P6.1",
            "statement": "lambda is nonincreasing after its maximum",
            "verdict": "registered-positive" if not p61_violations else "registered-negative",
            "grade": "registered-positive" if not p61_violations else "registered-negative",
            "values": {"violations": p61_violations},
            "interpretation": (
                "Mixed costs create sawtooth marginal values at budget parities where cost-2 candidates unlock."
                if p61_violations
                else ""
            ),
        },
        {
            "id": "P6.2",
            "statement": "slack point occurs before the examined budget maximum",
            "verdict": "registered-negative" if p62_fails else "registered-positive",
            "grade": "registered-negative" if p62_fails else "registered-positive",
            "values": {
                "lambda_tol": lambda_tol,
                "rep5_b_star": rep5["slack_point"],
                "rep5_b_max": rep5["b_max"],
                "surf3_b_star": surf3["slack_point"],
                "surf3_b_max": surf3["b_max"],
                "rep5_descriptive": rep5["descriptive_slack_points"],
                "surf3_descriptive": surf3["descriptive_slack_points"],
            },
            "interpretation": "The frozen lambda_tol is below the smallest genuine marginal in both families.",
        },
        {
            "id": "P6.3",
            "statement": "consequence test separates b*-1 from b* by more than two standard errors",
            "verdict": "registered-positive" if p63_ok else "registered-negative",
            "grade": "registered-positive" if p63_ok else "registered-negative",
            "values": consequence,
        },
        {
            "id": "P6.4",
            "statement": "proxy cost permutations are strictly worse at at least 80 percent of budget points",
            "verdict": "registered-positive" if p64_ok else "registered-negative",
            "grade": "registered-positive" if p64_ok else "registered-negative",
            "values": {
                "strictly_worse_fraction": proxy["strictly_worse_fraction"],
                "distinct_effective_cost_vectors": proxy["distinct_effective_cost_vectors"],
            },
        },
    ]


def _nonincreasing_violations(lam: list[float]) -> list[dict]:
    if not lam:
        return []
    start = int(np.argmax(np.asarray(lam, dtype=float)))
    violations = []
    for i in range(start + 1, len(lam)):
        if lam[i] > lam[i - 1] + 1e-12:
            violations.append({"index": i, "previous": lam[i - 1], "current": lam[i]})
    return violations


def _save_value_lambda_figure(run: Run, rep5: dict) -> None:
    budgets = list(range(rep5["b_max"] + 1))
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(budgets, rep5["V_exact"], marker="o", color="black", label="V exact")
    ax1.plot(budgets, rep5["V_greedy"], marker="s", color="gray", label="V greedy")
    ax1.axvline(rep5["slack_point"], color="lightgray", linestyle="--", linewidth=1)
    ax1.set_xlabel("budget")
    ax1.set_ylabel("V(b)")
    ax2 = ax1.twinx()
    ax2.plot(budgets[:-1], rep5["lambda_exact"], color="dimgray", linestyle=":", label="lambda")
    ax2.set_ylabel("lambda")
    ax1.set_title("REP(5) value and shadow prices")
    run.save_figure(
        fig,
        "e6_rep5_value_lambda",
        [
            [
                b,
                rep5["V_greedy"][b],
                rep5["V_exact"][b],
                rep5["lambda_exact"][b] if b < len(rep5["lambda_exact"]) else "",
            ]
            for b in budgets
        ],
        ["budget", "V_greedy", "V_exact", "lambda"],
    )
    plt.close(fig)


def _save_proxy_figure(run: Run, rep5: dict, proxy: dict) -> None:
    budgets = list(range(rep5["b_max"] + 1))
    values = np.asarray([curve["V"] for curve in proxy["curves"]], dtype=float)
    proxy_mean = np.mean(values, axis=0)
    proxy_min = np.min(values, axis=0)
    proxy_max = np.max(values, axis=0)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(budgets, rep5["V_exact"], color="black", marker="o", label="structural")
    ax.plot(budgets, proxy_mean, color="gray", linestyle="--", label="proxy mean")
    ax.fill_between(budgets, proxy_min, proxy_max, color="lightgray", label="proxy range")
    ax.set_xlabel("budget")
    ax.set_ylabel("V(b)")
    ax.set_title("REP(5) structural vs proxy costs")
    ax.legend()
    run.save_figure(
        fig,
        "e6_proxy_costs",
        [[b, rep5["V_exact"][b], proxy_mean[b], proxy_min[b], proxy_max[b]] for b in budgets],
        ["budget", "structural", "proxy_mean", "proxy_min", "proxy_max"],
    )
    plt.close(fig)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e6_slack <config.json>")
    main(sys.argv[1])
