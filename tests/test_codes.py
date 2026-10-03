import numpy as np
import pytest
from itertools import combinations

from sbqos.codes import canonical_rep, logical_flips, rep_code, surface_code, sympl, syndrome
from sbqos.linalg2 import rank_f2


def _single_error(n, q, pauli):
    e = np.zeros(2 * n, dtype=np.uint8)
    if pauli in {"X", "Y"}:
        e[q] = 1
    if pauli in {"Z", "Y"}:
        e[n + q] = 1
    return e


def test_rep3_middle_x_syndrome_and_canonical_rep():
    code = rep_code(3)
    middle_x = _single_error(code.n, 1, "X")

    np.testing.assert_array_equal(syndrome(code, middle_x), np.array([1, 1], dtype=np.uint8))
    np.testing.assert_array_equal(
        canonical_rep(code, np.array([1, 1], dtype=np.uint8)),
        middle_x,
    )


def test_surface3_detects_every_single_qubit_pauli_error():
    code = surface_code(3)

    for q in range(code.n):
        for pauli in ("X", "Y", "Z"):
            e = _single_error(code.n, q, pauli)
            assert np.any(syndrome(code, e)), (q, pauli)


def test_surface3_check_rank_and_logical_pairing():
    code = surface_code(3)

    assert rank_f2(np.vstack(code.checks)) == 8
    xbar, zbar = code.logicals
    assert sympl(xbar, zbar) == 1
    assert sympl(xbar, xbar) == 0


def test_surface3_logical_flips_for_xbar_error_by_name():
    code = surface_code(3)
    xbar_error = code.logicals[0].copy()

    flips = logical_flips(code, xbar_error)
    assert flips[0] == 0  # Xbar component: Xbar commutes with itself.
    assert flips[1] == 1  # Zbar component: Xbar anticommutes with Zbar.


def test_surface3_pairwise_commutation_unique_logical_anticommutation():
    code = surface_code(3)
    observables = code.checks + code.logicals
    xbar_index = len(code.checks)
    zbar_index = xbar_index + 1

    for i, a in enumerate(observables):
        for j, b in enumerate(observables):
            expected = 1 if (i, j) in {(xbar_index, zbar_index), (zbar_index, xbar_index)} else 0
            assert sympl(a, b) == expected, (i, j)


def test_surface5_rule_verifies_cleanly():
    code = surface_code(5)

    assert code.name == "SURF5"
    assert code.n == 25
    assert len(code.checks) == 24
    assert rank_f2(np.vstack(code.checks)) == 24
    assert sympl(code.logicals[0], code.logicals[1]) == 1


def test_code_meta_is_immutable():
    with pytest.raises(TypeError):
        rep_code(3).meta["x"] = 1
    with pytest.raises(TypeError):
        surface_code(3).meta["x"] = 1


@pytest.mark.parametrize("distance", [3, 5])
def test_surface_distance_is_exact_by_exhaustive_css_support_search(distance):
    code = surface_code(distance)
    # For a CSS code an undetected mixed error has undetected X and Z
    # components. If it is logically nontrivial, one component is nontrivial
    # and its weight is no larger. Searching pure components therefore proves
    # the full Pauli distance lower bound, without enumerating mixed labels.
    def mask(bits):
        return sum(int(bit) << q for q, bit in enumerate(bits))

    for check_half, logical_half in ((slice(code.n, 2 * code.n), code.logicals[1][code.n:]),
                                     (slice(0, code.n), code.logicals[0][:code.n])):
        checks = [mask(check[check_half]) for check in code.checks if np.any(check[check_half])]
        logical = mask(logical_half)
        for weight in range(1, distance):
            for support in combinations(range(code.n), weight):
                error = sum(1 << q for q in support)
                if all((check & error).bit_count() % 2 == 0 for check in checks):
                    assert (logical & error).bit_count() % 2 == 0, (distance, support)
    # The declared logical operators provide the matching upper bound.
    for logical in code.logicals:
        assert np.count_nonzero(logical[:code.n] | logical[code.n:]) == distance
        assert not np.any(syndrome(code, logical))
