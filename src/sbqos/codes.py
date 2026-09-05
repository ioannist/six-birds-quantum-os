"""Code dataclass; REP(d), SURF(3), SURF(5) constructors"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations, product
from types import MappingProxyType

import numpy as np

from sbqos.linalg2 import rank_f2

PauliVec = np.ndarray


@dataclass(frozen=True)
class Code:
    name: str
    n: int
    k: int
    checks: tuple[PauliVec, ...]
    logicals: tuple[PauliVec, ...]
    meta: Mapping[str, object]


_CANONICAL_CACHE: dict[str, dict[tuple[int, ...], PauliVec]] = {}


def _pauli(n: int, xs: tuple[int, ...] = (), zs: tuple[int, ...] = ()) -> PauliVec:
    v = np.zeros(2 * n, dtype=np.uint8)
    for q in xs:
        v[q] = 1
    for q in zs:
        v[n + q] = 1
    v.setflags(write=False)
    return v


def _pauli_weight(e: PauliVec) -> int:
    n = e.size // 2
    return int(np.count_nonzero((e[:n] | e[n:])))


def sympl(a: PauliVec, e: PauliVec) -> int:
    """Return the symplectic pairing of two Pauli vectors.

    Ref: design/01_MATH_SPEC.md §1.2.
    """
    a = np.asarray(a, dtype=np.uint8)
    e = np.asarray(e, dtype=np.uint8)
    if a.shape != e.shape or a.ndim != 1 or a.size % 2:
        raise ValueError("symplectic vectors must be 1D arrays of equal even length")
    n = a.size // 2
    return int((np.dot(a[:n], e[n:]) + np.dot(a[n:], e[:n])) % 2)


def rep_code(d: int) -> Code:
    """Construct REP(d) for d in {3, 5}.

    Ref: design/01_MATH_SPEC.md §1.1.
    """
    if d not in {3, 5}:
        raise ValueError("REP distance must be 3 or 5")

    checks = tuple(_pauli(d, zs=(i, i + 1)) for i in range(d - 1))
    # Xbar is kept for structural uniformity; REP+N1 D families should use Zbar only via code.logicals[1:].
    logicals = (_pauli(d, xs=tuple(range(d))), _pauli(d, zs=(0,)))
    return Code(name=f"REP{d}", n=d, k=1, checks=checks, logicals=logicals, meta=MappingProxyType({}))


# Qubit grid (0-indexed):
#     0   1   2
#     3   4   5
#     6   7   8
#
# Z-checks (pure-Z, detect X errors):
#   Z1 = {0,1,3,4}   bulk, top-left 2x2 block
#   Z2 = {4,5,7,8}   bulk, bottom-right 2x2 block
#   Z3 = {1,2}       boundary, top edge
#   Z4 = {6,7}       boundary, bottom edge
#
# X-checks (pure-X, detect Z errors):
#   X1 = {1,2,4,5}   bulk, top-right 2x2 block
#   X2 = {3,4,6,7}   bulk, bottom-left 2x2 block
#   X3 = {0,3}       boundary, left edge
#   X4 = {5,8}       boundary, right edge
#
# Logical Xbar = {0,1,2}   (top row, weight 3)
# Logical Zbar = {0,3,6}   (left column, weight 3)
_SURF3_Z_CHECKS = ((0, 1, 3, 4), (4, 5, 7, 8), (1, 2), (6, 7))
_SURF3_X_CHECKS = ((1, 2, 4, 5), (3, 4, 6, 7), (0, 3), (5, 8))


def surface_code(d: int) -> Code:
    """Construct SURF(d) for d in {3, 5}.

    Ref: design/01_MATH_SPEC.md §1.1.
    """
    if d == 3:
        z_checks, x_checks = _SURF3_Z_CHECKS, _SURF3_X_CHECKS
    elif d == 5:
        z3, x3 = _surface_supports_from_rule(3)
        if (z3, x3) != (_SURF3_Z_CHECKS, _SURF3_X_CHECKS):
            raise NotImplementedError("SURF(5) construction deferred — see report")
        z_checks, x_checks = _surface_supports_from_rule(5)
    else:
        raise ValueError("SURF distance must be 3 or 5")

    n = d * d
    checks = tuple(_pauli(n, zs=support) for support in z_checks)
    checks += tuple(_pauli(n, xs=support) for support in x_checks)
    logicals = (
        _pauli(n, xs=tuple(range(d))),
        _pauli(n, zs=tuple(d * r for r in range(d))),
    )
    code = Code(
        name=f"SURF{d}",
        n=n,
        k=1,
        checks=checks,
        logicals=logicals,
        meta=MappingProxyType({
            "grid_shape": (d, d),
            "qubit_pos": MappingProxyType({d * r + c: (r, c) for r in range(d) for c in range(d)}),
        }),
    )
    if d == 5 and not _surface5_verified(code):
        raise NotImplementedError("SURF(5) construction deferred — see report")
    return code


def syndrome(code: Code, e: PauliVec) -> np.ndarray:
    """Return check detection bits for an error.

    Ref: design/01_MATH_SPEC.md §1.2.
    """
    return np.array([sympl(h, e) for h in code.checks], dtype=np.uint8)


def logical_flips(code: Code, e: PauliVec) -> np.ndarray:
    """Return logical detection bits in code.logicals order.

    Ref: design/01_MATH_SPEC.md §1.2.
    """
    return np.array([sympl(logical, e) for logical in code.logicals], dtype=np.uint8)


def canonical_rep(code: Code, s: np.ndarray) -> PauliVec:
    """Return the deterministic minimum-weight representative for a syndrome.

    Ref: design/02_ARCHITECTURE.md §4.2.
    """
    table = _CANONICAL_CACHE.get(code.name)
    if table is None:
        table = _build_canonical_table(code)
        _CANONICAL_CACHE[code.name] = table

    key = tuple(int(x) for x in (np.asarray(s, dtype=np.uint8) & 1).tolist())
    try:
        return table[key].copy()
    except KeyError as exc:
        raise ValueError(f"unknown syndrome for {code.name}: {key}") from exc


def _surface_supports_from_rule(
    d: int,
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    z_checks: list[tuple[int, ...]] = []
    x_checks: list[tuple[int, ...]] = []

    for r in range(d - 1):
        for c in range(d - 1):
            _append_surface_anchor(d, r, c, z_checks, x_checks)

    for c in range(d - 1):
        _append_surface_anchor(d, -1, c, z_checks, x_checks, edge_type="Z")
    for c in range(d - 1):
        _append_surface_anchor(d, d - 1, c, z_checks, x_checks, edge_type="Z")
    for r in range(d - 1):
        _append_surface_anchor(d, r, -1, z_checks, x_checks, edge_type="X")
    for r in range(d - 1):
        _append_surface_anchor(d, r, d - 1, z_checks, x_checks, edge_type="X")

    return tuple(z_checks), tuple(x_checks)


def _append_surface_anchor(
    d: int,
    r: int,
    c: int,
    z_checks: list[tuple[int, ...]],
    x_checks: list[tuple[int, ...]],
    edge_type: str | None = None,
) -> None:
    rows = [row for row in (r, r + 1) if 0 <= row < d]
    cols = [col for col in (c, c + 1) if 0 <= col < d]
    if len(rows) * len(cols) == 1:
        return

    check_type = "Z" if (r + c) % 2 == 0 else "X"
    if edge_type is not None and check_type != edge_type:
        return

    support = tuple(d * row + col for row in rows for col in cols)
    if check_type == "Z":
        z_checks.append(support)
    else:
        x_checks.append(support)


def _surface5_verified(code: Code) -> bool:
    if code.n != 25 or len(code.checks) != 24:
        return False
    if rank_f2(np.vstack(code.checks)) != 24:
        return False
    if sympl(code.logicals[0], code.logicals[1]) != 1:
        return False
    observables = code.checks + code.logicals
    for i, a in enumerate(observables):
        for j, b in enumerate(observables):
            expected = 1 if {i, j} == {len(code.checks), len(code.checks) + 1} else 0
            if sympl(a, b) != expected:
                return False
    for h in code.checks:
        for logical in code.logicals:
            if sympl(h, logical):
                return False
    for q in range(code.n):
        for e in (
            _pauli(code.n, xs=(q,)),
            _pauli(code.n, zs=(q,)),
            _pauli(code.n, xs=(q,), zs=(q,)),
        ):
            if not np.any(syndrome(code, e)):
                return False
    return True


def _build_canonical_table(code: Code) -> dict[tuple[int, ...], PauliVec]:
    if code.name.startswith("REP"):
        return _build_rep_canonical_table(code)
    if code.name == "SURF3":
        return _build_surface3_canonical_table(code)
    raise NotImplementedError("canonical representatives for SURF(5) are deferred")


def _build_rep_canonical_table(code: Code) -> dict[tuple[int, ...], PauliVec]:
    table: dict[tuple[int, ...], PauliVec] = {}
    for bits in _patterns_by_weight_and_lex(code.n):
        e = _pauli(code.n, xs=tuple(i for i, bit in enumerate(bits) if bit))
        table.setdefault(tuple(int(x) for x in syndrome(code, e).tolist()), e)
        if len(table) == 2 ** len(code.checks):
            return table
    raise AssertionError(f"incomplete canonical table for {code.name}")


def _build_surface3_canonical_table(code: Code) -> dict[tuple[int, ...], PauliVec]:
    table: dict[tuple[int, ...], PauliVec] = {}
    errors: list[PauliVec] = []

    for weight in range(code.n + 1):
        for support in combinations(range(code.n), weight):
            for labels in product((1, 2, 3), repeat=weight):
                e = np.zeros(2 * code.n, dtype=np.uint8)
                for q, label in zip(support, labels):
                    if label & 1:
                        e[q] = 1
                    if label & 2:
                        e[code.n + q] = 1
                errors.append(e)
        errors.sort(key=lambda item: (_pauli_weight(item), tuple(int(x) for x in item.tolist())))
        for e in errors:
            table.setdefault(tuple(int(x) for x in syndrome(code, e).tolist()), e.copy())
        errors.clear()
        if len(table) == 2 ** len(code.checks):
            return table

    raise AssertionError("incomplete canonical table for SURF3")


def _patterns_by_weight_and_lex(n: int) -> list[tuple[int, ...]]:
    return sorted(product((0, 1), repeat=n), key=lambda bits: (sum(bits), bits))
