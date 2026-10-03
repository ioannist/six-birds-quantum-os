"""V(b), shadow prices, slack point, proxy null   MS §6"""

from __future__ import annotations

from fractions import Fraction
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
    costs: tuple[float | Fraction, ...],
    b_max: int,
) -> tuple[Fraction | float, ...]:
    """Enumerate all subsets; rational moments and costs stay exact.

    With a floating MomentEngine this is exhaustive optimization of approximate
    values. Float costs denote their exact binary rational values; pass Fraction
    costs when a decimal or rational budget boundary is intended.
    """
    if len(candidates.vecs) > 12:
        raise ValueError("exact value-curve subset cap exceeded")
    if len(costs) != len(candidates.vecs):
        raise ValueError("costs must have one entry per candidate")
    rational_costs = tuple(Fraction(cost) for cost in costs)
    if any(cost <= 0 for cost in rational_costs):
        raise ValueError("candidate costs must be positive")
    if b_max < 0:
        raise ValueError("b_max must be nonnegative")

    Xi0, _ = xi_residual(engine.cov_blocks(L0, D))
    trace0 = _trace_exact(Xi0) if engine.exact else _trace(Xi0)
    subset_values: list[tuple[Fraction, Fraction | float]] = []
    indices = tuple(range(len(candidates.vecs)))
    for size in range(len(indices) + 1):
        for subset in combinations(indices, size):
            cost = sum((rational_costs[i] for i in subset), Fraction(0))
            L_subset = _with_subset(L0, candidates, subset)
            Xi_subset, _ = xi_residual(engine.cov_blocks(L_subset, D))
            trace_subset = _trace_exact(Xi_subset) if engine.exact else _trace(Xi_subset)
            subset_values.append((cost, trace0 - trace_subset))

    values = []
    for b in range(b_max + 1):
        values.append(max(value for cost, value in subset_values if cost <= b))
    return tuple(values)


def shadow_prices(V: tuple[Fraction | float, ...]) -> tuple[Fraction | float, ...]:
    return tuple(V[b + 1] - V[b] for b in range(len(V) - 1))


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


def _trace_exact(M: Matrix) -> Fraction:
    return sum((M[i, i] for i in range(M.shape[0])), Fraction(0))
