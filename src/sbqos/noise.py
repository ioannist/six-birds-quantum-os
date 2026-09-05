"""NoiseModel dataclass; N1..N5 constructors; sampling"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from sbqos.codes import PauliVec

QubitDist = tuple[Fraction, Fraction, Fraction, Fraction]


@dataclass(frozen=True)
class Injection:
    prob: Fraction
    vec: PauliVec


@dataclass(frozen=True)
class HiddenSpec:
    kind: str
    transition_prob: Fraction
    mode_models: tuple["NoiseModel", "NoiseModel"]
    latch_qubit: int | None


@dataclass(frozen=True)
class NoiseModel:
    name: str
    per_qubit: tuple[QubitDist, ...]
    injection: Injection | None
    hidden: HiddenSpec | None


def n1(p: Fraction, n: int) -> NoiseModel:
    """Construct N1 iid bit-flip noise.

    Ref: design/01_MATH_SPEC.md §1.3.
    """
    p = Fraction(p)
    return NoiseModel("N1", tuple(_dist(1 - p, p, 0, 0) for _ in range(n)), None, None)


def n2(p: Fraction, n: int) -> NoiseModel:
    """Construct N2 iid depolarizing noise.

    Ref: design/01_MATH_SPEC.md §1.3.
    """
    p = Fraction(p)
    q = p / 3
    return NoiseModel("N2", tuple(_dist(1 - p, q, q, q) for _ in range(n)), None, None)


def n3(p: Fraction, q: Fraction, n: int, pair: tuple[int, int]) -> NoiseModel:
    """Construct N3 depolarizing noise plus correlated ZZ injection.

    Ref: design/01_MATH_SPEC.md §1.3.
    """
    base = n2(p, n)
    injection = Injection(Fraction(q), _pauli_vec(n, zs=pair))
    return NoiseModel("N3", base.per_qubit, injection, None)


def n4(p0: Fraction, s: Fraction, n: int) -> NoiseModel:
    """Construct N4 hidden alternating-mode drift noise.

    Ref: design/01_MATH_SPEC.md §1.3.
    """
    mode0 = n2(p0, n)
    mode1 = n2(3 * Fraction(p0), n)
    hidden = HiddenSpec("alternating", Fraction(s), (mode0, mode1), None)
    return NoiseModel("N4", mode0.per_qubit, None, hidden)


def n5(p: Fraction, r: Fraction, n: int, leak_qubit: int) -> NoiseModel:
    """Construct N5 latching leakage proxy noise.

    Ref: design/01_MATH_SPEC.md §1.3.
    """
    if not 0 <= leak_qubit < n:
        raise ValueError("leak_qubit out of range")

    mode0 = n2(p, n)
    mode1_per_qubit = list(mode0.per_qubit)
    mode1_per_qubit[leak_qubit] = _dist(Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4))
    mode1 = NoiseModel("N5_MODE1", tuple(mode1_per_qubit), None, None)
    hidden = HiddenSpec("latching", Fraction(r), (mode0, mode1), leak_qubit)
    return NoiseModel("N5", mode0.per_qubit, None, hidden)


def sample_error(
    model: NoiseModel,
    rng: np.random.Generator,
    mode_state: int | None = None,
) -> tuple[PauliVec, int | None]:
    """Sample one single-shot Pauli error and return the post-transition mode.

    For hidden models, mode_state is the incoming mode at the start of this
    round. The hidden-mode transition is applied first to obtain the round's
    actual mode, and the Pauli error is sampled from that new mode's
    distribution. The returned mode_state is that post-transition mode, not the
    incoming one. For non-hidden models, mode_state must be None and the error is
    sampled from the model directly.

    Ref: design/02_ARCHITECTURE.md §4.3.
    """
    if model.hidden is not None:
        if mode_state is None:
            raise ValueError("mode_state is required for models with hidden dynamics")
        new_mode = _next_mode(model.hidden, mode_state, rng)
        source = model.hidden.mode_models[new_mode]
    else:
        if mode_state is not None:
            raise ValueError("mode_state must be None for non-hidden models")
        new_mode = None
        source = model

    n = len(source.per_qubit)
    e = np.zeros(2 * n, dtype=np.uint8)
    for q, dist in enumerate(source.per_qubit):
        label = _draw_pauli(dist, rng)
        if label in {"X", "Y"}:
            e[q] = 1
        if label in {"Z", "Y"}:
            e[n + q] = 1

    if source.injection is not None and rng.random() < float(source.injection.prob):
        e ^= source.injection.vec

    return e, new_mode


def _next_mode(hidden: HiddenSpec, mode_state: int, rng: np.random.Generator) -> int:
    if mode_state not in {0, 1}:
        raise ValueError("mode_state must be 0 or 1")
    if hidden.kind == "alternating":
        flip = rng.random() < float(hidden.transition_prob)
        return 1 - mode_state if flip else mode_state
    if hidden.kind == "latching":
        if mode_state == 1:
            return 1
        latch = rng.random() < float(hidden.transition_prob)
        return 1 if latch else 0
    raise ValueError(f"unknown hidden kind: {hidden.kind!r}")


def _dist(pI: Fraction | int, pX: Fraction | int, pY: Fraction | int, pZ: Fraction | int) -> QubitDist:
    dist = (Fraction(pI), Fraction(pX), Fraction(pY), Fraction(pZ))
    if sum(dist, Fraction(0)) != 1:
        raise ValueError("qubit distribution must sum to 1")
    if any(p < 0 for p in dist):
        raise ValueError("qubit distribution probabilities must be nonnegative")
    return dist


def _pauli_vec(n: int, xs: tuple[int, ...] = (), zs: tuple[int, ...] = ()) -> PauliVec:
    v = np.zeros(2 * n, dtype=np.uint8)
    for q in xs:
        if not 0 <= q < n:
            raise ValueError("x-support qubit out of range")
        v[q] ^= 1
    for q in zs:
        if not 0 <= q < n:
            raise ValueError("z-support qubit out of range")
        v[n + q] ^= 1
    v.setflags(write=False)
    return v


def _draw_pauli(dist: QubitDist, rng: np.random.Generator) -> str:
    r = rng.random()
    pI, pX, pY, pZ = (float(p) for p in dist)
    if r < pI:
        return "I"
    if r < pI + pX:
        return "X"
    if r < pI + pX + pY:
        return "Y"
    if r < pI + pX + pY + pZ:
        return "Z"
    return "Z"
