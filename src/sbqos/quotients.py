"""exact predictive-quotient engine (EXACT only)   MS §5"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from types import MappingProxyType
from typing import Mapping

from sbqos.markov import rep3_n1_model


@dataclass(frozen=True)
class Package:
    states: tuple
    histories: tuple[tuple[Fraction, ...], ...]
    continuations: Mapping[str, tuple[tuple[Fraction, ...], ...]]
    now_events: tuple[tuple[Fraction, ...], ...]
    later_events: tuple[tuple[Fraction, ...], ...]
    later_pairs: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class QuotientResult:
    Q: tuple[frozenset[int], ...]
    M: tuple[frozenset[int], ...]
    pi_map: Mapping[int, tuple[int, ...]]
    witnesses: tuple[tuple[int, int], ...]
    max_fiber: int
    delta_max: Fraction


@dataclass(frozen=True)
class TransportMachine:
    nodes: tuple[frozenset[int], ...]
    edges: Mapping[tuple[int, str], int]


class QuotientPair:
    @staticmethod
    def compute(pkg: Package, iface: str = "now") -> QuotientResult:
        """Compute current and predictive quotients by exact signatures.

        Ref: design/01_MATH_SPEC.md §5.2.
        """
        if iface != "now":
            raise ValueError("iface must be 'now'")

        s0 = tuple(_s0(history, pkg.now_events) for history in pkg.histories)
        s_plus = tuple(_s_plus(history, pkg) for history in pkg.histories)
        Q = _partition_by_signature(s0)
        M = _partition_by_signature(s_plus)
        pi_map, witnesses, max_fiber, delta_max = _diagnostics(Q, M, s0, s_plus, len(pkg.later_pairs))

        return QuotientResult(
            Q=Q,
            M=M,
            pi_map=MappingProxyType(pi_map),
            witnesses=tuple(witnesses),
            max_fiber=max_fiber,
            delta_max=delta_max,
        )


def transport_check(pkg: Package, M: tuple[frozenset[int], ...]) -> TransportMachine:
    """Check predictive transport is well-defined on M-classes.

    Ref: design/01_MATH_SPEC.md §5.3.
    """
    s_plus = tuple(_s_plus(history, pkg) for history in pkg.histories)
    signature_to_m = {}
    for m_idx, group in enumerate(M):
        representative = next(iter(group))
        signature = s_plus[representative]
        signature_to_m[signature] = m_idx

    edges = {}
    for gamma, continuation in pkg.continuations.items():
        for m_idx, group in enumerate(M):
            target_signature = None
            for h_idx in group:
                pushed = _push(pkg.histories[h_idx], continuation)
                pushed_signature = _s_plus(pushed, pkg)
                if target_signature is None:
                    target_signature = pushed_signature
                elif pushed_signature != target_signature:
                    raise ValueError(f"transport ill-defined for continuation {gamma!r}, M-class {m_idx}")
            if target_signature not in signature_to_m:
                raise ValueError(f"transport target missing for continuation {gamma!r}, M-class {m_idx}")
            edges[(m_idx, gamma)] = signature_to_m[target_signature]

    return TransportMachine(nodes=M, edges=MappingProxyType(edges))


def currentization_search(
    pkg: Package,
    candidates: tuple[tuple[Fraction, ...], ...],
) -> tuple[frozenset[int], ...]:
    """Find minimal candidate now-events that eliminate predictive witnesses.

    Ref: design/01_MATH_SPEC.md §5.4.
    """
    if len(candidates) > 12:
        raise ValueError("currentization candidate search cap exceeded")

    s_plus = tuple(_s_plus(history, pkg) for history in pkg.histories)
    M = _partition_by_signature(s_plus)
    for size in range(len(candidates) + 1):
        passing = []
        for subset in combinations(range(len(candidates)), size):
            now_events = pkg.now_events + tuple(candidates[i] for i in subset)
            s0 = tuple(_s0(history, now_events) for history in pkg.histories)
            Q = _partition_by_signature(s0)
            _pi_map, witnesses, max_fiber, _delta_max = _diagnostics(Q, M, s0, s_plus, len(pkg.later_pairs))
            if len(witnesses) == 0 and max_fiber == 1:
                passing.append(frozenset(subset))
        if passing:
            return tuple(passing)
    return ()


def internalize_schedule(
    pkg: Package,
    phases: tuple[tuple[tuple[Fraction, ...], ...], ...],
    alpha: Fraction,
) -> Package:
    """Internalize a declared phase schedule by random-scan lifting.

    Ref: design/01_MATH_SPEC.md §5.5.
    """
    num_phases = len(phases)
    if num_phases == 0:
        raise ValueError("phases must be nonempty")
    if len(pkg.states) % num_phases != 0:
        raise ValueError("number of states must divide evenly by number of phases")

    alpha = Fraction(alpha)
    n_base = len(pkg.states) // num_phases
    n_joint = len(pkg.states)
    rows = [[Fraction(0) for _ in range(n_joint)] for _ in range(n_joint)]
    for base in range(n_base):
        for phase in range(num_phases):
            i = base * num_phases + phase
            j_tick = base * num_phases + ((phase + 1) % num_phases)
            rows[i][j_tick] += alpha
            for next_base, weight in enumerate(phases[phase][base]):
                if weight != 0:
                    j_update = next_base * num_phases + phase
                    rows[i][j_update] += (Fraction(1) - alpha) * weight

    one_round = tuple(tuple(row) for row in rows)
    two_rounds = _matmul(one_round, one_round)
    continuations = MappingProxyType({"one_round": one_round, "two_rounds": two_rounds})
    later_pairs = tuple(("two_rounds", event_idx) for event_idx in range(len(pkg.later_events)))
    return Package(
        states=pkg.states,
        histories=pkg.histories,
        continuations=continuations,
        now_events=pkg.now_events,
        later_events=pkg.later_events,
        later_pairs=later_pairs,
    )


def rep3_n1_package(decoder: str = "minimum_weight") -> Package:
    """Build the REP(3)+N1 memoryless quotient package.

    This audit-purpose catalog is for the T5 witness/quotient-cardinality
    check, not transport closure; transport_check is expected to raise on it.
    See design/01_MATH_SPEC.md §5.3.

    Ref: design/05_IMPLEMENTATION_PLAN.md §T5.
    """
    model = rep3_n1_model(decoder, exact=True)
    states = model.states
    n_states = len(states)

    histories = []
    for syndrome in sorted(set(int(x) for x in model.lens_syndrome)):
        fiber = [i for i, value in enumerate(model.lens_syndrome) if int(value) == syndrome]
        mass = Fraction(1, len(fiber))
        histories.append(tuple(mass if i in fiber else Fraction(0) for i in range(n_states)))

    now_events = tuple(
        tuple(Fraction((int(model.lens_syndrome[i]) >> b) & 1) for i in range(n_states))
        for b in range(model.n_syndrome_bits)
    )
    later_events = now_events + tuple(
        tuple(Fraction((int(model.lens_decoded[i]) >> b) & 1) for i in range(n_states))
        for b in range(model.n_logical_bits)
    )
    one_round = _matrix_tuple(model.P)
    two_rounds = _matmul(one_round, one_round)
    continuations = MappingProxyType({"one_round": one_round, "two_rounds": two_rounds})
    later_pairs = tuple(
        (gamma, event_idx) for gamma in ("one_round", "two_rounds") for event_idx in range(len(later_events))
    )

    return Package(
        states=states,
        histories=tuple(histories),
        continuations=continuations,
        now_events=now_events,
        later_events=later_events,
        later_pairs=later_pairs,
    )


def _s0(history: tuple[Fraction, ...], now_events: tuple[tuple[Fraction, ...], ...]) -> tuple[Fraction, ...]:
    return tuple(_obs(history, event) for event in now_events)


def _s_plus(history: tuple[Fraction, ...], pkg: Package) -> tuple[Fraction, ...]:
    values = []
    for continuation_name, event_idx in pkg.later_pairs:
        pushed = _push(history, pkg.continuations[continuation_name])
        values.append(_obs(pushed, pkg.later_events[event_idx]))
    return tuple(values)


def _obs(history: tuple[Fraction, ...], event: tuple[Fraction, ...]) -> Fraction:
    return sum((h_i * e_i for h_i, e_i in zip(history, event)), Fraction(0))


def _push(
    history: tuple[Fraction, ...],
    continuation: tuple[tuple[Fraction, ...], ...],
) -> tuple[Fraction, ...]:
    n = len(history)
    return tuple(
        sum((history[i] * continuation[i][j] for i in range(n)), Fraction(0))
        for j in range(n)
    )


def _partition_by_signature(signatures: tuple[tuple[Fraction, ...], ...]) -> tuple[frozenset[int], ...]:
    groups: dict[tuple[Fraction, ...], list[int]] = {}
    for idx, signature in enumerate(signatures):
        groups.setdefault(signature, []).append(idx)
    return tuple(frozenset(indices) for indices in groups.values())


def _diagnostics(
    Q: tuple[frozenset[int], ...],
    M: tuple[frozenset[int], ...],
    s0: tuple[tuple[Fraction, ...], ...],
    s_plus: tuple[tuple[Fraction, ...], ...],
    later_pairs_length: int,
) -> tuple[dict[int, tuple[int, ...]], tuple[tuple[int, int], ...], int, Fraction]:
    history_to_m: dict[int, int] = {}
    for m_idx, group in enumerate(M):
        for h_idx in group:
            history_to_m[h_idx] = m_idx

    pi_map = {}
    for q_idx, group in enumerate(Q):
        pi_map[q_idx] = tuple(sorted({history_to_m[h_idx] for h_idx in group}))

    witnesses: list[tuple[int, int]] = []
    delta_max = Fraction(0)
    for i in range(len(s0)):
        for j in range(i + 1, len(s0)):
            if s0[i] == s0[j] and s_plus[i] != s_plus[j]:
                witnesses.append((i, j))
                pair_delta = max(
                    (abs(s_plus[i][k] - s_plus[j][k]) for k in range(later_pairs_length)),
                    default=Fraction(0),
                )
                delta_max = max(delta_max, pair_delta)

    max_fiber = max((len(v) for v in pi_map.values()), default=0)
    return pi_map, tuple(witnesses), max_fiber, delta_max


def _matrix_tuple(matrix) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(entry if isinstance(entry, Fraction) else Fraction(entry) for entry in row) for row in matrix)


def _matmul(
    A: tuple[tuple[Fraction, ...], ...],
    B: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    rows = len(A)
    cols = len(B[0]) if B else 0
    inner = len(B)
    return tuple(
        tuple(sum((A[i][k] * B[k][j] for k in range(inner)), Fraction(0)) for j in range(cols))
        for i in range(rows)
    )
