from fractions import Fraction

import pytest

from sbqos import rng
from sbqos.codes import rep_code
from sbqos.moments import MomentEngine, ProbeFamily
from sbqos.noise import n1
from sbqos.prices import proxy_costs, shadow_prices, slack_point, value_curve, value_curve_exact
from sbqos.xi import xi_residual


def test_rep3_n1_value_curve_greedy_matches_exact_ground_truth():
    code = rep_code(3)
    model = n1(Fraction(1, 20), code.n)
    engine = MomentEngine(model, exact=True)
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    L0 = ProbeFamily("native", (), ())
    candidates = ProbeFamily(
        "candidate",
        code.checks + (code.checks[0].copy(),),
        ("h0", "h1", "h0_dup"),
    )
    costs = (1.0, 1.0, 1.0)
    expected = (
        0.0,
        0.08502762430939227,
        0.10632022900763359,
        0.10632022900763359,
    )

    Xi0, _ = xi_residual(engine.cov_blocks(L0, D))
    assert float(Xi0[0, 0]) == pytest.approx(0.19)
    greedy = value_curve(engine, L0, D, candidates, costs, b_max=3)
    exact = value_curve_exact(engine, L0, D, candidates, costs, b_max=3)

    assert greedy == pytest.approx(expected, abs=1e-12)
    assert exact == pytest.approx(expected, abs=1e-12)
    assert greedy == pytest.approx(exact, abs=1e-9)


def test_shadow_prices_and_slack_point_match_ground_truth():
    V = (
        0.0,
        0.08502762430939227,
        0.10632022900763359,
        0.10632022900763359,
    )

    lam = shadow_prices(V)

    assert lam == pytest.approx((0.08502762430939227, 0.021292604698241322, 0.0), abs=1e-15)
    assert slack_point(lam, tol=1e-9) == 2


def test_slack_point_suffix_not_first_dip():
    assert slack_point((0.2, 0.0, 0.1, 0.0), tol=1e-9) == 3
    assert slack_point((0.2,), tol=1e-9) == 1
    assert slack_point((), tol=1e-9) == 0


def test_proxy_costs_same_multiset_and_deterministic():
    costs = (1.0, 2.0, 1.0)

    p1 = proxy_costs(costs, rng(7))
    p2 = proxy_costs(costs, rng(7))

    assert p1 == p2
    assert sorted(p1) == sorted(costs)


def test_value_curve_exact_rejects_large_candidate_set():
    code = rep_code(3)
    model = n1(Fraction(1, 20), code.n)
    engine = MomentEngine(model, exact=True)
    D = ProbeFamily("logical", (code.logicals[1],), ("Zbar",))
    L0 = ProbeFamily("native", (), ())
    candidates = ProbeFamily("candidate", tuple(code.checks[0].copy() for _ in range(13)), tuple(str(i) for i in range(13)))

    with pytest.raises(ValueError, match="subset cap"):
        value_curve_exact(engine, L0, D, candidates, tuple(1.0 for _ in range(13)), b_max=1)
