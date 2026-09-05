"""Phase-0 diagnostics for the E2 W2 witness result.

Ref: design/06_W2_PHASE2.md §2.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import inf, log
from typing import Callable

import numpy as np

from sbqos.codes import Code
from sbqos.moments import CovBlocks, MomentEngine, ProbeFamily
from sbqos.noise import NoiseModel
from sbqos.streams import ShotTable, sample_shots
from sbqos.xi import xi_residual


def signal_budget(declared_model: NoiseModel, truth_model: NoiseModel, L: ProbeFamily, D: ProbeFamily) -> dict:
    """Return exact mean/covariance drift budgets and the A*-lifted W2 signal."""
    declared_engine = MomentEngine(declared_model, exact=True)
    truth_engine = MomentEngine(truth_model, exact=True)

    delta_mean_L = tuple(
        truth_engine.mean(vec) - declared_engine.mean(vec)
        for vec in L.vecs
    )
    delta_mean_norm_sq = sum(float(x) ** 2 for x in delta_mean_L)

    declared_blocks = declared_engine.cov_blocks(L, D)
    truth_blocks = truth_engine.cov_blocks(L, D)
    delta_K_LL = np.asarray(truth_blocks.K_LL, dtype=object) - np.asarray(declared_blocks.K_LL, dtype=object)
    delta_K_LL_frobenius_sq = float(np.sum(np.asarray(delta_K_LL, dtype=float) ** 2))

    _Xi_declared, A_star = xi_residual(declared_blocks)
    # A_star is computed from exact Fraction blocks above; the diagnostic lift is
    # reported on the floating matrix scale used by the deployed W2 statistic.
    A = np.asarray(A_star, dtype=float)
    delta_D_lifted = A @ np.asarray(delta_K_LL, dtype=float) @ A.T
    delta_D_lifted_frobenius_sq = float(np.sum(delta_D_lifted ** 2))

    return {
        "delta_mean_L": delta_mean_L,
        "delta_mean_L_norm_sq": delta_mean_norm_sq,
        "delta_K_LL": delta_K_LL,
        "delta_K_LL_frobenius_sq": delta_K_LL_frobenius_sq,
        "A_star": A_star,
        "delta_D_lifted": delta_D_lifted,
        "delta_D_lifted_frobenius_sq": delta_D_lifted_frobenius_sq,
    }


def own_null_scale(
    code: Code,
    model: NoiseModel,
    L: ProbeFamily,
    D: ProbeFamily,
    N: int,
    B: int,
    rng: np.random.Generator,
    statistic_fn: Callable[[ShotTable, CovBlocks], float],
) -> float:
    """Return the 99th percentile of a pluggable statistic under the declared null."""
    model_blocks = MomentEngine(model, exact=False).cov_blocks(L, D)
    values = []
    for _ in range(B):
        shots_b = sample_shots(code, model, L, D, N, rng)
        values.append(float(statistic_fn(shots_b, model_blocks)))
    return float(np.percentile(np.asarray(values, dtype=float), 99.0))


def full_syndrome_pmf(engine: MomentEngine, L: ProbeFamily) -> dict[tuple[int, ...], Fraction]:
    """Recover the exact full native-check syndrome pmf by WHT inversion."""
    k = len(L.vecs)
    n = engine.n
    coeff: dict[tuple[int, ...], Fraction] = {}
    for subset in product((0, 1), repeat=k):
        vec = np.zeros(2 * n, dtype=np.uint8)
        for bit, probe in zip(subset, L.vecs):
            if bit:
                vec ^= probe
        value = engine.mean(vec)
        if not isinstance(value, Fraction):
            raise ValueError("full_syndrome_pmf requires an exact MomentEngine")
        coeff[subset] = value

    scale = Fraction(1, 2**k)
    pmf: dict[tuple[int, ...], Fraction] = {}
    for syndrome in product((0, 1), repeat=k):
        total = Fraction(0)
        for subset, value in coeff.items():
            parity = sum(a & b for a, b in zip(subset, syndrome)) % 2
            total += value if parity == 0 else -value
        pmf[syndrome] = scale * total

    if sum(pmf.values(), Fraction(0)) != Fraction(1):
        raise ValueError("full syndrome pmf does not sum to one exactly")
    if any(prob < 0 for prob in pmf.values()):
        raise ValueError("full syndrome pmf contains a negative probability")
    return pmf


def syndrome_kl(declared_pmf: dict[tuple[int, ...], Fraction], truth_pmf: dict[tuple[int, ...], Fraction]) -> float:
    """Return D_KL(truth || declared) in nats per shot."""
    total = 0.0
    for key, p1_frac in truth_pmf.items():
        if p1_frac == 0:
            continue
        p0_frac = declared_pmf[key]
        if p0_frac == 0:
            return inf
        p1 = float(p1_frac)
        p0 = float(p0_frac)
        total += p1 * log(p1 / p0)
    return float(total)


def bernoulli_kl(p1: float, p0: float) -> float:
    """Return Bernoulli D_KL(p1 || p0) in nats."""
    return _kl_term(p1, p0) + _kl_term(1.0 - p1, 1.0 - p0)


def _kl_term(a: float, b: float) -> float:
    if a == 0.0:
        return 0.0
    if b == 0.0:
        return inf
    return float(a * log(a / b))
