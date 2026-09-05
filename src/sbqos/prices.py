"""V(b), shadow prices, slack point, proxy null   MS §6"""

from __future__ import annotations

from itertools import combinations

import numpy as np

from sbqos.moments import Matrix, MomentEngine, ProbeFamily
from sbqos.xi import select_checks, xi_residual


def value_curve(
    engine: MomentEngine,
    L0: ProbeFamily,
    D: ProbeFamily,
    candidates: ProbeFamily,
    costs: tuple[float, ...],
    b_max: int,
) -> tuple[float, ...]:
    """Greedy lower-bound value curve V(b).

    Ref: design/01_MATH_SPEC.md §6.
    """
    Xi0, _ = xi_residual(engine.cov_blocks(L0, D))
    trace0 = _trace(Xi0)
    values = []
    for b in range(b_max + 1):
        log = select_checks(engine, L0, D, candidates, costs, budget=float(b), tol_stop=1e-12)
        values.append(trace0 - log.final_residual_trace)
    return tuple(values)


def value_curve_exact(
    engine: MomentEngine,
    L0: ProbeFamily,
    D: ProbeFamily,
    candidates: ProbeFamily,
    costs: tuple[float, ...],
    b_max: int,
) -> tuple[float, ...]:
    """Exhaustively enumerate candidate subsets to compute exact V(b)."""
    if len(candidates.vecs) > 12:
        raise ValueError("exact value-curve subset cap exceeded")
    if len(costs) != len(candidates.vecs):
        raise ValueError("costs must have one entry per candidate")

    Xi0, _ = xi_residual(engine.cov_blocks(L0, D))
    trace0 = _trace(Xi0)
    subset_values: list[tuple[float, float]] = []
    indices = tuple(range(len(candidates.vecs)))
    for size in range(len(indices) + 1):
        for subset in combinations(indices, size):
            cost = sum(float(costs[i]) for i in subset)
            L_subset = _with_subset(L0, candidates, subset)
            Xi_subset, _ = xi_residual(engine.cov_blocks(L_subset, D))
            subset_values.append((cost, trace0 - _trace(Xi_subset)))

    values = []
    for b in range(b_max + 1):
        values.append(max((value for cost, value in subset_values if cost <= float(b)), default=0.0))
    return tuple(values)


def shadow_prices(V: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(float(V[b + 1]) - float(V[b]) for b in range(len(V) - 1))


def slack_point(lam: tuple[float, ...], tol: float) -> int:
    b_star = len(lam)
    for b in range(len(lam) - 1, -1, -1):
        if lam[b] <= tol:
            b_star = b
        else:
            break
    return b_star


def proxy_costs(costs: tuple[float, ...], rng: np.random.Generator) -> tuple[float, ...]:
    return tuple(float(x) for x in rng.permutation(np.asarray(costs, dtype=float)))


def _with_subset(L0: ProbeFamily, candidates: ProbeFamily, subset: tuple[int, ...]) -> ProbeFamily:
    return ProbeFamily(
        role=L0.role,
        vecs=L0.vecs + tuple(candidates.vecs[i] for i in subset),
        labels=L0.labels + tuple(candidates.labels[i] for i in subset),
    )


def _trace(M: Matrix) -> float:
    return float(np.trace(np.asarray(M, dtype=float)))
