"""F2 linear algebra: rank, solve, row-reduce (uint8 matrices)"""

from __future__ import annotations

import numpy as np


def _as_f2_matrix(M: np.ndarray) -> np.ndarray:
    A = np.asarray(M, dtype=np.uint8)
    if A.ndim != 2:
        raise ValueError("expected a 2D matrix")
    return (A & 1).copy()


def rank_f2(M: np.ndarray) -> int:
    """Return the row rank over GF(2).

    Ref: design/02_ARCHITECTURE.md §4.1.
    """
    _, pivots = row_reduce_f2(M)
    return len(pivots)


def row_reduce_f2(M: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Return reduced row-echelon form over GF(2) and pivot columns.

    Ref: design/02_ARCHITECTURE.md §4.1.
    """
    R = _as_f2_matrix(M)
    n_rows, n_cols = R.shape
    pivots: list[int] = []
    row = 0

    for col in range(n_cols):
        if row == n_rows:
            break

        pivot_offsets = np.flatnonzero(R[row:, col])
        if pivot_offsets.size == 0:
            continue

        pivot = row + int(pivot_offsets[0])
        if pivot != row:
            R[[row, pivot]] = R[[pivot, row]]

        for other in range(n_rows):
            if other != row and R[other, col]:
                R[other] ^= R[row]

        pivots.append(col)
        row += 1

    return R, pivots


def in_span_f2(M: np.ndarray, v: np.ndarray) -> bool:
    """Return whether v is in the row span of M over GF(2).

    Ref: design/02_ARCHITECTURE.md §4.1.
    """
    A = _as_f2_matrix(M)
    b = np.asarray(v, dtype=np.uint8).reshape(1, -1) & 1
    if A.shape[1] != b.shape[1]:
        raise ValueError("matrix and vector widths differ")
    return rank_f2(A) == rank_f2(np.vstack([A, b]))
