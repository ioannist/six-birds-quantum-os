from fractions import Fraction
from dataclasses import replace

import pytest

from sbqos.quotients import (
    Package,
    QuotientPair,
    currentization_search,
    internalize_schedule,
    rep3_n1_package,
    transport_check,
)


def test_two_history_toy_quotient_result_exact():
    pkg = Package(
        states=(0, 1),
        histories=((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))),
        continuations={"identity": ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))},
        now_events=((Fraction(0), Fraction(0)),),
        later_events=((Fraction(0), Fraction(1)),),
        later_pairs=(("identity", 0),),
    )

    result = QuotientPair.compute(pkg)

    assert result.Q == (frozenset({0, 1}),)
    assert set(result.M) == {frozenset({0}), frozenset({1})}
    assert len(result.pi_map[0]) == 2
    assert set(result.pi_map[0]) == {0, 1}
    assert result.witnesses == ((0, 1),)
    assert result.max_fiber == 2
    assert result.delta_max == Fraction(1)


def test_quotient_pair_rejects_unsupported_iface():
    pkg = Package(
        states=(),
        histories=(),
        continuations={},
        now_events=(),
        later_events=(),
        later_pairs=(),
    )

    with pytest.raises(ValueError, match="iface must be 'now'"):
        QuotientPair.compute(pkg, iface="later")


def test_rep3_n1_memoryless_package_has_no_predictive_witnesses():
    pkg = rep3_n1_package()
    result = QuotientPair.compute(pkg)

    assert len(result.Q) == 4
    assert len(result.M) == 4
    assert len(result.Q) == len(result.M)
    assert result.witnesses == ()


def test_rep3_n1_package_is_not_transport_closed_by_design():
    pkg = rep3_n1_package()
    result = QuotientPair.compute(pkg)

    # Intentional per design/01_MATH_SPEC.md §5.3: this is an audit catalog, not a transport-closed one.
    with pytest.raises(ValueError, match="transport target missing"):
        transport_check(pkg, result.M)


def test_transport_check_well_defined_two_node_machine():
    pkg = _transport_pkg(
        {
            "identity": _identity(4),
            "good": _permutation_matrix((2, 3, 0, 1)),
        }
    )
    result = QuotientPair.compute(pkg)

    machine = transport_check(pkg, result.M)

    low = result.M.index(frozenset({0, 1}))
    high = result.M.index(frozenset({2, 3}))
    assert machine.nodes == result.M
    assert machine.edges[(low, "identity")] == low
    assert machine.edges[(high, "identity")] == high
    assert machine.edges[(low, "good")] == high
    assert machine.edges[(high, "good")] == low


def test_transport_check_raises_on_ill_defined_continuation():
    pkg = _transport_pkg(
        {
            "identity": _identity(4),
            "bad": _permutation_matrix((2, 1, 0, 3)),
        }
    )
    result = QuotientPair.compute(pkg)

    with pytest.raises(ValueError, match="transport ill-defined"):
        transport_check(pkg, result.M)


def test_currentization_search_hidden_bit_candidate_passes_at_cardinality_one():
    pkg = _two_history_toy_pkg()
    candidates = ((Fraction(0), Fraction(1)),)

    assert currentization_search(pkg, candidates) == (frozenset({0}),)


def test_currentization_search_rejects_oversized_candidate_catalog():
    pkg = _two_history_toy_pkg()
    candidates = tuple((Fraction(0), Fraction(0)) for _ in range(13))

    with pytest.raises(ValueError, match="search cap"):
        currentization_search(pkg, candidates)


def test_internalize_schedule_kills_two_phase_protocol_trap_at_two_rounds():
    naive_pkg = _alternating_schedule_naive_pkg()

    naive_result = QuotientPair.compute(naive_pkg)
    assert naive_result.Q == (frozenset({0, 1}), frozenset({2, 3}))
    assert naive_result.witnesses == ((0, 1), (2, 3))

    phases = (
        ((Fraction(0), Fraction(1)), (Fraction(1), Fraction(0))),
        ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))),
    )
    internalized = internalize_schedule(naive_pkg, phases, Fraction(1, 2))
    expected_one = (
        (Fraction(0), Fraction(1, 2), Fraction(1, 2), Fraction(0)),
        (Fraction(1, 2), Fraction(1, 2), Fraction(0), Fraction(0)),
        (Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)),
        (Fraction(0), Fraction(0), Fraction(1, 2), Fraction(1, 2)),
    )
    expected_two = (
        (Fraction(1, 2), Fraction(1, 4), Fraction(0), Fraction(1, 4)),
        (Fraction(1, 4), Fraction(1, 2), Fraction(1, 4), Fraction(0)),
        (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)),
        (Fraction(1, 4), Fraction(0), Fraction(1, 4), Fraction(1, 2)),
    )

    assert internalized.continuations["one_round"] == expected_one
    assert internalized.continuations["two_rounds"] == expected_two
    for matrix in (expected_one, expected_two):
        for row in matrix:
            assert sum(row, Fraction(0)) == Fraction(1)

    internalized_result = QuotientPair.compute(internalized)
    assert internalized.later_pairs == (("two_rounds", 0),)
    assert internalized_result.witnesses == ()

    one_round_pkg = Package(
        states=internalized.states,
        histories=internalized.histories,
        continuations=internalized.continuations,
        now_events=internalized.now_events,
        later_events=internalized.later_events,
        later_pairs=(("one_round", 0),),
    )
    one_round_result = QuotientPair.compute(one_round_pkg)
    assert one_round_result.witnesses != ()
    assert (0, 1) in one_round_result.witnesses


def _two_history_toy_pkg() -> Package:
    return Package(
        states=(0, 1),
        histories=((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))),
        continuations={"identity": ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))},
        now_events=((Fraction(0), Fraction(0)),),
        later_events=((Fraction(0), Fraction(1)),),
        later_pairs=(("identity", 0),),
    )


def _transport_pkg(continuations) -> Package:
    return Package(
        states=(0, 1, 2, 3),
        histories=(
            (Fraction(1), Fraction(0), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(1), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(1), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(0), Fraction(1)),
        ),
        continuations=continuations,
        now_events=((Fraction(0), Fraction(0), Fraction(0), Fraction(0)),),
        later_events=((Fraction(0), Fraction(0), Fraction(1), Fraction(1)),),
        later_pairs=(("identity", 0),),
    )


def _alternating_schedule_naive_pkg() -> Package:
    return Package(
        states=((0, "A"), (0, "B"), (1, "A"), (1, "B")),
        histories=(
            (Fraction(1), Fraction(0), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(1), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(1), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(0), Fraction(1)),
        ),
        continuations={"one_round": _permutation_matrix((3, 0, 1, 2))},
        now_events=((Fraction(0), Fraction(0), Fraction(1), Fraction(1)),),
        later_events=((Fraction(0), Fraction(0), Fraction(1), Fraction(1)),),
        later_pairs=(("one_round", 0),),
    )


def _identity(n: int):
    return tuple(
        tuple(Fraction(1) if i == j else Fraction(0) for j in range(n))
        for i in range(n)
    )


def _permutation_matrix(targets: tuple[int, ...]):
    return tuple(
        tuple(Fraction(1) if j == target else Fraction(0) for j in range(len(targets)))
        for target in targets
    )


def test_comparison_map_requires_identity_or_actual_refinement():
    result = QuotientPair.compute(_two_history_toy_pkg())
    assert dict(result.comparison_map) == {0: 0, 1: 0}
    # A one-step erasure kernel makes futures equal but preserves distinct now
    # signatures. The all-continuations theorem cannot be imported here.
    pkg = replace(_two_history_toy_pkg(),
                  now_events=((Fraction(0), Fraction(1)),),
                  continuations={"identity": ((Fraction(1), Fraction(0)), (Fraction(1), Fraction(0)))})
    erased = QuotientPair.compute(pkg)
    assert len(erased.M) == 1 and len(erased.Q) == 2
    with pytest.raises(ValueError, match="does not refine"):
        _ = erased.comparison_map


@pytest.mark.parametrize("changes", [
    {"histories": ((Fraction(1, 2), Fraction(0)),)},
    {"histories": ((Fraction(1),),)},
    {"now_events": ((Fraction(1),),)},
    {"later_events": ((Fraction(0), Fraction(2)),)},
    {"histories": ((1.0, 0.0),)},
    {"continuations": {"identity": ((Fraction(1), Fraction(1)), (Fraction(0), Fraction(1)))}},
    {"later_pairs": (("missing", 0),)},
    {"later_pairs": (("identity", -1),)},
])
def test_invalid_probability_packages_cannot_issue_certificates(changes):
    with pytest.raises(ValueError):
        replace(_two_history_toy_pkg(), **changes)


def test_transport_rejects_a_partition_that_is_not_the_predictive_quotient():
    pkg = _two_history_toy_pkg()
    with pytest.raises(ValueError, match="predictive partition"):
        transport_check(pkg, (frozenset({0, 1}),))


def test_internalization_rejects_nonstochastic_phase_data():
    pkg = _alternating_schedule_naive_pkg()
    with pytest.raises(ValueError, match="alpha"):
        internalize_schedule(pkg, (_identity(2), _identity(2)), Fraction(3, 2))
    with pytest.raises(ValueError, match="phase kernels"):
        internalize_schedule(pkg, (((Fraction(-1), Fraction(2)), (Fraction(0), Fraction(1))), _identity(2)), Fraction(1, 2))
