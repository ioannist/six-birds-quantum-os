"""xi_residual, witness, discharge, greedy   MS §3"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from sbqos.moments import CovBlocks, CovBlocksExt, Matrix, MomentEngine, ProbeFamily


@dataclass(frozen=True)
class Witness:
    lam_max: float
    z: np.ndarray
    labels: tuple[str, ...]


@dataclass(frozen=True)
class CandidateRanking:
    candidate_label: str
    value: float
    cost: float
    value_per_cost: float
    feasible: bool


@dataclass(frozen=True)
class SelectionRound:
    rankings: tuple[CandidateRanking, ...]
    selected_label: str | None
    cumulative_cost: float


@dataclass(frozen=True)
class SelectionLog:
    rounds: tuple[SelectionRound, ...]
    selected_indices: tuple[int, ...]
    final_residual_trace: float


def xi_residual(blocks: CovBlocks) -> tuple[Matrix, Matrix]:
    """Return the adequacy residual Xi(D|L) and optimal linear map A_star.

    The prototype's Ξ is the conditional covariance of logical ±1 observables given scheduled-check ±1 observables (optionally augmented with degree-2 products). Ξ = 0 certifies exact coverage by the linear estimator class over the declared feature family; Ξ ≻ 0 certifies a coverage gap for that class and prices it. It does **not** assert that no nonlinear decoder covers the gap. The degree ladder (E3b) shows the residual contracting as feature degree grows, which is the framework's own account of what nonlinear decoding buys ([XI] chain rule; [CAST] budgeted-randomness curve).

    Ref: design/01_MATH_SPEC.md §3.1.
    """
    K_LL_pinv = _pinv(blocks.K_LL)
    K_DL = _matrix(blocks.K_DL)
    K_DD = _matrix(blocks.K_DD)
    K_LD = K_DL.T
    A_star = K_DL @ K_LL_pinv
    Xi = K_DD - K_DL @ K_LL_pinv @ K_LD
    return Xi, A_star


def psd_check(Xi: Matrix, tol: float) -> bool:
    """Return whether Xi is PSD up to a float tolerance.

    Ref: design/01_MATH_SPEC.md §3.1.
    """
    M = _as_float_matrix(Xi)
    M = (M + M.T) / 2.0
    eigvals = np.linalg.eigvalsh(M)
    return bool(np.min(eigvals) >= -tol)


def blind_spot_witness(Xi: Matrix, Omega: Matrix, labels: tuple[str, ...]) -> Witness:
    """Return the top eigenpair of Xi - Omega.

    Ref: design/01_MATH_SPEC.md §3.2.
    """
    Delta = _as_float_matrix(Xi) - _as_float_matrix(Omega)
    Delta = (Delta + Delta.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(Delta)
    z = eigenvectors[:, -1]
    return Witness(float(eigenvalues[-1]), z, labels)


def discharge(blocks_ext: CovBlocksExt, M_indices: tuple[int, ...]) -> tuple[Matrix, float]:
    """Return discharge matrix and trace value for candidate indices.

    Ref: design/01_MATH_SPEC.md §3.3.
    """
    if not M_indices:
        n_d = blocks_ext.K_DD.shape[0]
        D_matrix = _zero_matrix(n_d, n_d, _is_exact_matrix(blocks_ext.K_DD))
        return D_matrix, 0.0

    ix = np.ix_(M_indices, M_indices)
    K_MM_sub = _matrix(blocks_ext.K_MM)[ix]
    K_DM_sub = _matrix(blocks_ext.K_DM)[:, M_indices]
    K_ML_sub = _matrix(blocks_ext.K_ML)[M_indices, :]
    K_LM_sub = K_ML_sub.T
    K_LL_pinv = _pinv(blocks_ext.K_LL)
    K_DL = _matrix(blocks_ext.K_DL)

    K_MM_given_L = K_MM_sub - K_ML_sub @ K_LL_pinv @ K_LM_sub
    K_DM_given_L = K_DM_sub - K_DL @ K_LL_pinv @ K_LM_sub
    K_MM_given_L_pinv = _pinv(K_MM_given_L)
    D_matrix = K_DM_given_L @ K_MM_given_L_pinv @ K_DM_given_L.T
    return D_matrix, _trace_float(D_matrix)


def chain_rule_check(
    engine: MomentEngine,
    L: ProbeFamily,
    D: ProbeFamily,
    M: ProbeFamily,
) -> float:
    """Return max absolute chain-rule discrepancy.

    Ref: design/01_MATH_SPEC.md §3.3.
    """
    blocks = engine.cov_blocks(L, D)
    Xi_L, _ = xi_residual(blocks)
    ext = engine.extend_blocks(blocks, M)
    D_matrix, _ = discharge(ext, tuple(range(len(M.vecs))))
    L_union = ProbeFamily(
        role=L.role,
        vecs=L.vecs + M.vecs,
        labels=L.labels + M.labels,
    )
    Xi_union, _ = xi_residual(engine.cov_blocks(L_union, D))
    predicted = _matrix(Xi_L) - _matrix(D_matrix)
    diff = _as_float_matrix(Xi_union) - _as_float_matrix(predicted)
    if diff.size == 0:
        return 0.0
    return float(np.max(np.abs(diff)))


def select_checks(
    engine: MomentEngine,
    L0: ProbeFamily,
    D: ProbeFamily,
    candidates: ProbeFamily,
    costs: tuple[float, ...],
    budget: float,
    tol_stop: float,
) -> SelectionLog:
    """Greedily select checks by discharge value per cost.

    Ref: design/01_MATH_SPEC.md §3.4.
    """
    if len(costs) != len(candidates.vecs):
        raise ValueError("costs must have one entry per candidate")
    if any(cost <= 0 for cost in costs):
        raise ValueError("candidate costs must be positive")

    remaining = list(range(len(candidates.vecs)))
    selected: list[int] = []
    rounds: list[SelectionRound] = []
    cumulative_cost = 0.0

    while remaining:
        L_current = _current_family(L0, candidates, selected)
        blocks = engine.cov_blocks(L_current, D)
        ext = engine.extend_blocks(blocks, candidates)
        rankings: list[tuple[bool, float, float, int, CandidateRanking]] = []
        remaining_budget = budget - cumulative_cost
        for i in remaining:
            _, value = discharge(ext, (i,))
            value_per_cost = value / costs[i]
            feasible = costs[i] <= remaining_budget
            ranking = CandidateRanking(
                candidate_label=candidates.labels[i],
                value=value,
                cost=float(costs[i]),
                value_per_cost=value_per_cost,
                feasible=feasible,
            )
            rankings.append((feasible, value_per_cost, value, -i, ranking))

        rankings.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
        ordered_rankings = tuple(item[4] for item in rankings)
        selectable = [
            (value_per_cost, value, -neg_i)
            for feasible, value_per_cost, value, neg_i, _ranking in rankings
            if feasible and value >= tol_stop
        ]
        if not selectable:
            rounds.append(
                SelectionRound(
                    rankings=ordered_rankings,
                    selected_label=None,
                    cumulative_cost=cumulative_cost,
                )
            )
            break

        value_per_cost, value, best = selectable[0]
        cumulative_cost += costs[best]
        selected.append(best)
        remaining.remove(best)
        rounds.append(
            SelectionRound(
                rankings=ordered_rankings,
                selected_label=candidates.labels[best],
                cumulative_cost=cumulative_cost,
            )
        )

    L_final = _current_family(L0, candidates, selected)
    Xi_final, _ = xi_residual(engine.cov_blocks(L_final, D))
    return SelectionLog(
        rounds=tuple(rounds),
        selected_indices=tuple(selected),
        final_residual_trace=_trace_float(Xi_final),
    )


def greedy_select(*args, **kwargs) -> SelectionLog:
    """Alias for select_checks.

    Ref: design/02_ARCHITECTURE.md §4.5.
    """
    return select_checks(*args, **kwargs)


def _current_family(L0: ProbeFamily, candidates: ProbeFamily, selected: list[int]) -> ProbeFamily:
    return ProbeFamily(
        role=L0.role,
        vecs=L0.vecs + tuple(candidates.vecs[i] for i in selected),
        labels=L0.labels + tuple(candidates.labels[i] for i in selected),
    )


def _pinv(M: Matrix) -> Matrix:
    if _is_exact_matrix(M):
        return _pinv_fraction(M)
    return np.linalg.pinv(np.asarray(M, dtype=float), rcond=1e-12)


def _pinv_fraction(M: Matrix) -> Matrix:
    A = _fraction_matrix(M)
    n_rows, n_cols = A.shape
    if n_rows != n_cols:
        raise ValueError("pseudoinverse helper expects a square matrix")

    indices = _independent_row_indices(A)
    result = np.empty((n_rows, n_cols), dtype=object)
    result[:, :] = Fraction(0)
    if not indices:
        return result

    C = A[:, indices]
    G = _frac_matmul(C.T, C)
    G_inv = _inverse_fraction(G)
    K_SS = A[np.ix_(indices, indices)]
    return _frac_matmul(C, G_inv, K_SS, G_inv, C.T)


def _independent_row_indices(A: Matrix) -> list[int]:
    rows = [[A[i, j] for j in range(A.shape[1])] for i in range(A.shape[0])]
    row_ids = list(range(A.shape[0]))
    pivots: list[int] = []
    row = 0

    for col in range(A.shape[1]):
        pivot = next((r for r in range(row, len(rows)) if rows[r][col] != 0), None)
        if pivot is None:
            continue
        rows[row], rows[pivot] = rows[pivot], rows[row]
        row_ids[row], row_ids[pivot] = row_ids[pivot], row_ids[row]
        pivot_val = rows[row][col]
        rows[row] = [x / pivot_val for x in rows[row]]
        for r in range(len(rows)):
            if r != row and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [x - factor * y for x, y in zip(rows[r], rows[row])]
        pivots.append(row_ids[row])
        row += 1
        if row == len(rows):
            break

    return pivots


def _inverse_fraction(A: Matrix) -> Matrix:
    n_rows, n_cols = A.shape
    if n_rows != n_cols:
        raise ValueError("inverse helper expects a square matrix")

    left = [[A[i, j] for j in range(n_cols)] for i in range(n_rows)]
    right = [[Fraction(int(i == j)) for j in range(n_rows)] for i in range(n_rows)]

    for col in range(n_cols):
        pivot = next((r for r in range(col, n_rows) if left[r][col] != 0), None)
        if pivot is None:
            raise ValueError("singular matrix in exact inverse")
        left[col], left[pivot] = left[pivot], left[col]
        right[col], right[pivot] = right[pivot], right[col]
        pivot_val = left[col][col]
        left[col] = [x / pivot_val for x in left[col]]
        right[col] = [x / pivot_val for x in right[col]]
        for r in range(n_rows):
            if r != col and left[r][col] != 0:
                factor = left[r][col]
                left[r] = [x - factor * y for x, y in zip(left[r], left[col])]
                right[r] = [x - factor * y for x, y in zip(right[r], right[col])]

    inv = np.empty((n_rows, n_cols), dtype=object)
    for i in range(n_rows):
        for j in range(n_cols):
            inv[i, j] = right[i][j]
    return inv


def _frac_matmul(*matrices: Matrix) -> Matrix:
    if not matrices:
        raise ValueError("at least one matrix is required")
    result = _fraction_matrix(matrices[0])
    for matrix in matrices[1:]:
        B = _fraction_matrix(matrix)
        if result.shape[1] != B.shape[0]:
            raise ValueError("matrix dimensions do not align")
        product = np.empty((result.shape[0], B.shape[1]), dtype=object)
        for i in range(result.shape[0]):
            for j in range(B.shape[1]):
                product[i, j] = sum(
                    (result[i, k] * B[k, j] for k in range(result.shape[1])),
                    Fraction(0),
                )
        result = product
    return result


def _is_exact_matrix(M: Matrix) -> bool:
    A = np.asarray(M)
    return A.dtype == object or any(isinstance(x, Fraction) for x in A.flat)


def _fraction_matrix(M: Matrix) -> Matrix:
    A = np.asarray(M)
    result = np.empty(A.shape, dtype=object)
    for idx in np.ndindex(A.shape):
        result[idx] = A[idx] if isinstance(A[idx], Fraction) else Fraction(A[idx])
    return result


def _matrix(M: Matrix) -> Matrix:
    return _fraction_matrix(M) if _is_exact_matrix(M) else np.asarray(M, dtype=float)


def _zero_matrix(rows: int, cols: int, exact: bool) -> Matrix:
    if exact:
        result = np.empty((rows, cols), dtype=object)
        result[:, :] = Fraction(0)
        return result
    return np.zeros((rows, cols), dtype=float)


def _as_float_matrix(M: Matrix) -> np.ndarray:
    A = np.asarray(M)
    result = np.empty(A.shape, dtype=float)
    for idx in np.ndindex(A.shape):
        result[idx] = float(A[idx])
    return result


def _trace_float(M: Matrix) -> float:
    A = np.asarray(M)
    if A.size == 0:
        return 0.0
    return float(sum(float(A[i, i]) for i in range(min(A.shape))))
