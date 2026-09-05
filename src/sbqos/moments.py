"""MomentEngine (EXACT-capable)          MS §2"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

import numpy as np

from sbqos.codes import PauliVec, sympl
from sbqos.noise import NoiseModel

Matrix = np.ndarray


@dataclass(frozen=True)
class ProbeFamily:
    role: str
    vecs: tuple[PauliVec, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True)
class CovBlocks:
    L: ProbeFamily
    D: ProbeFamily
    K_LL: Matrix
    K_DL: Matrix
    K_DD: Matrix


@dataclass(frozen=True)
class CovBlocksExt:
    L: ProbeFamily
    D: ProbeFamily
    M: ProbeFamily
    K_LL: Matrix
    K_DL: Matrix
    K_DD: Matrix
    K_MM: Matrix
    K_DM: Matrix
    K_ML: Matrix


class MomentEngine:
    """Closed-form ±1 moment engine for stochastic Pauli noise.

    Ref: design/01_MATH_SPEC.md §2.
    """

    def __init__(self, model: NoiseModel, exact: bool):
        if model.hidden is not None:
            raise ValueError("hidden-mode moments require engine_for_mode")
        self.model = model
        self.exact = exact
        self.n = len(model.per_qubit)
        self._cache: dict[bytes, Fraction | float] = {}
        if exact:
            self._per_qubit = model.per_qubit
            self._injection_prob = model.injection.prob if model.injection is not None else None
            self._one = Fraction(1)
            self._zero = Fraction(0)
        else:
            self._per_qubit = tuple(tuple(float(p) for p in dist) for dist in model.per_qubit)
            self._injection_prob = float(model.injection.prob) if model.injection is not None else None
            self._one = 1.0
            self._zero = 0.0

    def mean(self, a: PauliVec) -> Fraction | float:
        """Return E[sigma_a].

        Ref: design/01_MATH_SPEC.md §2.2.
        """
        vec = self._as_vec(a)
        key = bytes(vec)
        if key in self._cache:
            return self._cache[key]

        value = self._one
        for q, dist in enumerate(self._per_qubit):
            ax = int(vec[q])
            az = int(vec[self.n + q])
            value *= self._single_factor(ax, az, dist)

        if self.model.injection is not None:
            sign = 1 if sympl(vec, self.model.injection.vec) == 0 else -1
            if self.exact:
                q = self._injection_prob
                value *= (Fraction(1) - q) + q * sign
            else:
                q = self._injection_prob
                value *= (1.0 - q) + q * float(sign)

        self._cache[key] = value
        return value

    def cov(self, a: PauliVec, b: PauliVec) -> Fraction | float:
        """Return Cov(sigma_a, sigma_b).

        Ref: design/01_MATH_SPEC.md §2.3.
        """
        av = self._as_vec(a)
        bv = self._as_vec(b)
        if av.shape != bv.shape:
            raise ValueError("covariance vectors must have the same shape")
        return self.mean(av ^ bv) - self.mean(av) * self.mean(bv)

    def cov_blocks(self, L: ProbeFamily, D: ProbeFamily) -> CovBlocks:
        """Build covariance blocks for L and D probe families.

        Ref: design/01_MATH_SPEC.md §2.3.
        """
        return CovBlocks(
            L=L,
            D=D,
            K_LL=self._cov_matrix(L.vecs, L.vecs),
            K_DL=self._cov_matrix(D.vecs, L.vecs),
            K_DD=self._cov_matrix(D.vecs, D.vecs),
        )

    def extend_blocks(self, blocks: CovBlocks, M: ProbeFamily) -> CovBlocksExt:
        """Extend covariance blocks with a candidate probe family M.

        Ref: design/02_ARCHITECTURE.md §4.4.
        """
        return CovBlocksExt(
            L=blocks.L,
            D=blocks.D,
            M=M,
            K_LL=blocks.K_LL,
            K_DL=blocks.K_DL,
            K_DD=blocks.K_DD,
            K_MM=self._cov_matrix(M.vecs, M.vecs),
            K_DM=self._cov_matrix(blocks.D.vecs, M.vecs),
            K_ML=self._cov_matrix(M.vecs, blocks.L.vecs),
        )

    def _cov_matrix(self, rows: tuple[PauliVec, ...], cols: tuple[PauliVec, ...]) -> Matrix:
        matrix = np.empty((len(rows), len(cols)), dtype=object if self.exact else np.float64)
        for i, a in enumerate(rows):
            for j, b in enumerate(cols):
                matrix[i, j] = self.cov(a, b)
        return matrix

    def _as_vec(self, a: PauliVec) -> np.ndarray:
        vec = np.asarray(a, dtype=np.uint8) & 1
        if vec.ndim != 1 or vec.size != 2 * self.n:
            raise ValueError("Pauli vector has wrong shape for this model")
        return vec

    def _single_factor(self, ax: int, az: int, dist) -> Fraction | float:
        total = self._zero
        for prob, px, pz in zip(dist, (0, 1, 1, 0), (0, 0, 1, 1)):
            bit = (ax * pz + az * px) % 2
            total += prob * (1 if bit == 0 else -1)
        return total


def engine_for_mode(model: NoiseModel, m: int, exact: bool) -> MomentEngine:
    """Return a moment engine for hidden mode m.

    Ref: design/02_ARCHITECTURE.md §4.4.
    """
    if model.hidden is None:
        raise ValueError("model has no hidden modes")
    if m not in {0, 1}:
        raise ValueError("mode index must be 0 or 1")
    return MomentEngine(model.hidden.mode_models[m], exact=exact)


def degree2_family(L: ProbeFamily) -> ProbeFamily:
    """Return L plus all pairwise XOR degree-2 probes.

    Ref: design/01_MATH_SPEC.md §2.4.
    """
    vecs = list(L.vecs)
    labels = list(L.labels)
    for i, j in combinations(range(len(L.vecs)), 2):
        vec = (L.vecs[i] ^ L.vecs[j]).astype(np.uint8)
        vec.setflags(write=False)
        vecs.append(vec)
        labels.append(f"{L.labels[i]}^{L.labels[j]}")
    return ProbeFamily(role=L.role, vecs=tuple(vecs), labels=tuple(labels))
