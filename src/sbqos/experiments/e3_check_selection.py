"""E3 check-selection and degree-ladder experiment runner."""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations, product
from time import perf_counter

import numpy as np

from sbqos import rng as project_rng
from sbqos.artifacts import Run, parse_fraction
from sbqos.codes import Code, logical_flips, rep_code, surface_code, syndrome
from sbqos.experiments.common import main_template, setup_matplotlib
from sbqos.moments import MomentEngine, ProbeFamily, degree2_family
from sbqos.noise import n1, n2
from sbqos.xi import select_checks, xi_residual

setup_matplotlib()
import matplotlib.pyplot as plt


def main(config_path: str) -> None:
    main_template(config_path, _run)


def _run(config: dict, run: Run) -> None:
    seed = int(config["seed"])
    surf3_p = parse_fraction(config["surf3_p"])
    rep3_p = parse_fraction(config["rep3_p"])
    surf5_p = parse_fraction(config["surf5_p"])
    n_random = int(config["n_random_baselines"])
    tol_stop = float(config["tol_stop"])

    surf3 = _surf3_sweep(surf3_p, seed, n_random, tol_stop)
    rep3 = _rep3_ladder(rep3_p, tol_stop)
    surf5 = _surf5_spot(surf5_p)
    predictions = _predictions(surf3, rep3, surf5, tol_stop)

    results = {
        "experiment": "e3",
        "claim_grade": "exact-finite",
        "surf3_greedy": surf3,
        "rep3_ladder": rep3,
        "surf5_spot": surf5,
        "predictions": predictions,
    }
    run.write_result(results)
    _save_budget_figure(run, surf3)
    _save_ladder_figure(run, rep3)


def _surf3_sweep(p: Fraction, seed: int, n_random: int, tol_stop: float) -> dict:
    code = surface_code(3)
    engine = MomentEngine(n2(p, code.n), exact=True)
    L0 = ProbeFamily("native", (), ())
    D = ProbeFamily("logical", code.logicals, ("Xbar", "Zbar"))
    candidates = _checks_family(code)
    costs = tuple(1.0 for _ in candidates.vecs)

    baseline_trace = _trace(xi_residual(engine.cov_blocks(L0, D))[0])
    full_log = select_checks(engine, L0, D, candidates, costs, budget=float(len(candidates.vecs)), tol_stop=tol_stop)
    greedy_order = [candidates.labels[i] for i in full_log.selected_indices]
    greedy = []
    for b in range(0, len(candidates.vecs) + 1):
        if b == 0:
            trace = baseline_trace
        else:
            trace = select_checks(engine, L0, D, candidates, costs, budget=float(b), tol_stop=tol_stop).final_residual_trace
        greedy.append({"budget": b, "trace_xi": trace})

    lex = _trace_for_order(engine, L0, D, candidates, tuple(range(len(candidates.vecs))))
    random_curves = []
    for i in range(n_random):
        gen = project_rng(seed + i)
        order = tuple(int(x) for x in gen.permutation(len(candidates.vecs)))
        random_curves.append({"seed": seed + i, "order": [candidates.labels[j] for j in order], "curve": _trace_for_order(engine, L0, D, candidates, order)})

    violations = _baseline_violations(greedy, lex, random_curves)
    return {
        "baseline_trace": baseline_trace,
        "greedy_order": greedy_order,
        "greedy_curve": greedy,
        "lex_curve": lex,
        "random_curves": random_curves,
        "baseline_violations": violations,
    }


def _trace_for_order(
    engine: MomentEngine,
    L0: ProbeFamily,
    D: ProbeFamily,
    candidates: ProbeFamily,
    order: tuple[int, ...],
) -> list[dict]:
    rows = []
    for b in range(0, len(order) + 1):
        selected = order[:b]
        L = _with_indices(L0, candidates, selected)
        rows.append({"budget": b, "trace_xi": _trace(xi_residual(engine.cov_blocks(L, D))[0])})
    return rows


def _baseline_violations(greedy: list[dict], lex: list[dict], random_curves: list[dict]) -> list[dict]:
    violations = []
    for b in range(1, len(greedy)):
        greedy_trace = greedy[b]["trace_xi"]
        if lex[b]["trace_xi"] < greedy_trace - 1e-12:
            violations.append({"baseline": "lex", "budget": b, "baseline_trace": lex[b]["trace_xi"], "greedy_trace": greedy_trace})
        for curve in random_curves:
            trace = curve["curve"][b]["trace_xi"]
            if trace < greedy_trace - 1e-12:
                violations.append({"baseline": f"random_{curve['seed']}", "budget": b, "baseline_trace": trace, "greedy_trace": greedy_trace})
    return violations


def _rep3_ladder(p: Fraction, tol_stop: float) -> dict:
    code = rep_code(3)
    engine = MomentEngine(n1(p, code.n), exact=True)
    L_degree1 = _checks_family(code)
    L_degree2 = degree2_family(L_degree1)
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    trace1 = _trace(xi_residual(engine.cov_blocks(L_degree1, D))[0])
    Xi2, _ = xi_residual(engine.cov_blocks(L_degree2, D))
    trace2 = _trace(Xi2)
    mmse = _rep3_exact_mmse(code, p)

    candidates = ProbeFamily(
        "candidate",
        L_degree1.vecs + L_degree2.vecs,
        ("h0", "h1", "h0_dup", "h1_dup", "h0^h1"),
    )
    log = select_checks(
        engine,
        ProbeFamily("native", (), ()),
        D,
        candidates,
        tuple(1.0 for _ in candidates.vecs),
        budget=10.0,
        tol_stop=tol_stop,
    )
    duplicate_values = []
    selected_so_far: set[str] = set()
    for round_info in log.rounds:
        selected = round_info.selected_label
        for ranking in round_info.rankings:
            original = {"h0_dup": "h0", "h1_dup": "h1"}.get(ranking.candidate_label)
            if original in selected_so_far and selected != ranking.candidate_label:
                duplicate_values.append({"label": ranking.candidate_label, "value": ranking.value})
        if selected is not None:
            selected_so_far.add(selected)

    return {
        "rungs": [
            {"rung": 1, "label": "degree1", "trace_xi": trace1},
            {"rung": 2, "label": "degree2_complete", "trace_xi": trace2},
        ],
        "exact_mmse": float(mmse),
        "exact_mmse_fraction": f"{mmse.numerator}/{mmse.denominator}",
        "rung2_minus_mmse": trace2 - float(mmse),
        "monotone": trace2 <= trace1 + 1e-12,
        "mmse_equal": abs(trace2 - float(mmse)) <= 1e-10,
        "selection": {
            "selected_labels": [candidates.labels[i] for i in log.selected_indices],
            "selected_count": len(log.selected_indices),
            "candidate_count": len(candidates.vecs),
            "final_round_selected_label": log.rounds[-1].selected_label if log.rounds else None,
            "duplicate_passover_values": duplicate_values,
        },
    }


def _rep3_exact_mmse(code: Code, p: Fraction) -> Fraction:
    groups: dict[tuple[int, ...], list[tuple[Fraction, int]]] = {}
    for bits in product((0, 1), repeat=code.n):
        e = np.zeros(2 * code.n, dtype=np.uint8)
        weight = sum(bits)
        for q, bit in enumerate(bits):
            e[q] = bit
        prob = (p**weight) * ((Fraction(1) - p) ** (code.n - weight))
        key = tuple(int(x) for x in syndrome(code, e))
        zbar = 1 - 2 * int(logical_flips(code, e)[1])
        groups.setdefault(key, []).append((prob, zbar))

    mmse = Fraction(0)
    for entries in groups.values():
        mass = sum((prob for prob, _z in entries), Fraction(0))
        mean = sum((prob * z for prob, z in entries), Fraction(0)) / mass
        for prob, z in entries:
            mmse += prob * (Fraction(z) - mean) ** 2
    return mmse


def _surf5_spot(p: Fraction) -> dict:
    start = perf_counter()
    code = surface_code(5)
    engine = MomentEngine(n2(p, code.n), exact=False)
    L_degree1 = _checks_family(code)
    D = ProbeFamily("logical", code.logicals, ("Xbar", "Zbar"))
    trace_degree1 = _trace(xi_residual(engine.cov_blocks(L_degree1, D))[0])
    capped = _adjacent_degree2_family(L_degree1, code.n)
    L_augmented = ProbeFamily(
        "native",
        L_degree1.vecs + capped["family"].vecs,
        L_degree1.labels + capped["family"].labels,
    )
    trace_augmented = _trace(xi_residual(engine.cov_blocks(L_augmented, D))[0])
    elapsed = perf_counter() - start
    return {
        "trace_degree1": trace_degree1,
        "trace_degree1_plus_capped_degree2": trace_augmented,
        "contraction": trace_degree1 - trace_augmented,
        "cap_log": {
            "total_degree2_pairs": capped["total_pairs"],
            "kept_adjacent_pairs": capped["kept_pairs"],
            "dropped_pairs": capped["dropped_pairs"],
        },
        "runtime_under_two_minutes": elapsed < 120.0,
    }


def _adjacent_degree2_family(L: ProbeFamily, n: int) -> dict:
    supports = [_support(vec, n) for vec in L.vecs]
    vecs = []
    labels = []
    total = 0
    for i, j in combinations(range(len(L.vecs)), 2):
        total += 1
        if supports[i] & supports[j]:
            vecs.append((L.vecs[i] ^ L.vecs[j]).astype(np.uint8))
            labels.append(f"{L.labels[i]}^{L.labels[j]}")
    return {
        "family": ProbeFamily("candidate", tuple(vecs), tuple(labels)),
        "total_pairs": total,
        "kept_pairs": len(vecs),
        "dropped_pairs": total - len(vecs),
    }


def _support(vec, n: int) -> set[int]:
    return {i for i in range(n) if int(vec[i]) or int(vec[n + i])}


def _predictions(surf3: dict, rep3: dict, surf5: dict, tol_stop: float) -> list[dict]:
    p31_ok = not surf3["baseline_violations"]
    duplicate_values = rep3["selection"]["duplicate_passover_values"]
    p33_ok = bool(duplicate_values) and all(row["value"] < tol_stop for row in duplicate_values)
    p34_ok = (
        rep3["selection"]["selected_count"] < rep3["selection"]["candidate_count"]
        and rep3["selection"]["final_round_selected_label"] is None
    )
    return [
        {
            "id": "P3.1",
            "statement": "greedy residual is no worse than tested baselines at every budget",
            "verdict": "registered-positive" if p31_ok else "registered-negative",
            "grade": "registered-positive" if p31_ok else "registered-negative",
            "values": {"violations": surf3["baseline_violations"]},
        },
        {
            "id": "P3.2",
            "statement": "degree ladder is monotone and top rung equals exact MMSE",
            "verdict": "registered-positive" if rep3["monotone"] and rep3["mmse_equal"] else "registered-negative",
            "grade": "registered-positive" if rep3["monotone"] and rep3["mmse_equal"] else "registered-negative",
            "values": {
                "monotone": rep3["monotone"],
                "rung2_minus_mmse": rep3["rung2_minus_mmse"],
                "exact_mmse_fraction": rep3["exact_mmse_fraction"],
            },
        },
        {
            "id": "P3.3",
            "statement": "duplicate candidates have zero marginal value when passed over",
            "verdict": "registered-positive" if p33_ok else "registered-negative",
            "grade": "registered-positive" if p33_ok else "registered-negative",
            "values": {"duplicate_passover_values": duplicate_values},
        },
        {
            "id": "P3.4",
            "statement": "greedy stops before exhausting duplicate-containing candidate list",
            "verdict": "registered-positive" if p34_ok else "registered-negative",
            "grade": "registered-positive" if p34_ok else "registered-negative",
            "values": rep3["selection"],
        },
    ]


def _checks_family(code: Code) -> ProbeFamily:
    return ProbeFamily("native", code.checks, tuple(f"h{i}" for i in range(len(code.checks))))


def _with_indices(L0: ProbeFamily, candidates: ProbeFamily, selected: tuple[int, ...]) -> ProbeFamily:
    return ProbeFamily(
        L0.role,
        L0.vecs + tuple(candidates.vecs[i] for i in selected),
        L0.labels + tuple(candidates.labels[i] for i in selected),
    )


def _save_budget_figure(run: Run, surf3: dict) -> None:
    greedy = surf3["greedy_curve"]
    lex = surf3["lex_curve"]
    random_curves = surf3["random_curves"]
    budgets = [row["budget"] for row in greedy]
    random_values = np.array([[curve["curve"][b]["trace_xi"] for b in budgets] for curve in random_curves], dtype=float)
    random_mean = np.mean(random_values, axis=0)
    random_min = np.min(random_values, axis=0)
    random_max = np.max(random_values, axis=0)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(budgets, [row["trace_xi"] for row in greedy], marker="o", label="greedy", color="black")
    ax.plot(budgets, [row["trace_xi"] for row in lex], marker="s", label="lex", color="gray")
    ax.fill_between(budgets, random_min, random_max, color="lightgray", label="random range")
    ax.plot(budgets, random_mean, linestyle="--", color="dimgray", label="random mean")
    ax.set_xlabel("budget")
    ax.set_ylabel("tr Xi")
    ax.set_title("SURF(3) coverage by budget")
    ax.legend()
    run.save_figure(
        fig,
        "e3_coverage_vs_budget",
        [
            [b, greedy[b]["trace_xi"], lex[b]["trace_xi"], random_mean[b], random_min[b], random_max[b]]
            for b in budgets
        ],
        ["budget", "greedy", "lex", "random_mean", "random_min", "random_max"],
    )
    plt.close(fig)


def _save_ladder_figure(run: Run, rep3: dict) -> None:
    rows = rep3["rungs"]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot([row["rung"] for row in rows], [row["trace_xi"] for row in rows], marker="o", color="black")
    ax.axhline(rep3["exact_mmse"], color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("rung")
    ax.set_ylabel("tr Xi")
    ax.set_title("REP(3) degree ladder")
    run.save_figure(
        fig,
        "e3_degree_ladder",
        [[row["rung"], row["trace_xi"], rep3["exact_mmse"]] for row in rows],
        ["rung", "trace_xi", "mmse_floor"],
    )
    plt.close(fig)


def _trace(M) -> float:
    return float(np.trace(np.asarray(M, dtype=float)))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m sbqos.experiments.e3_check_selection <config.json>")
    main(sys.argv[1])
