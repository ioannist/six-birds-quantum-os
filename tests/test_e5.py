import json
from pathlib import Path
from fractions import Fraction
from dataclasses import replace
from copy import deepcopy

import pytest
import numpy as np

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e5_decoder_memory import (
    _belief_machine,
    _packaged_machine_minimality,
    _posterior,
    _payoff_hidden,
    _payoff_v2_deltas,
    _payoff_v2_exact_filter,
    _payoff_v2_point,
    _payoff_v2_rounding_gap,
    _syndrome_likelihood,
    main,
)
from sbqos.markov import rep3_n4_model
from sbqos.noise import n4


CONFIG_PATH = Path("src/sbqos/configs/e5.json")


@pytest.fixture(scope="module")
def e5_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e5")
    config = load_config(str(CONFIG_PATH))
    config["payoff_rounds"] = 2000
    config["payoff_v2_rounds"] = 2000
    config["belief_bfs_depth"] = 3
    config_path = tmp_path / "e5.json"
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")

    original = common.run_dir_for
    run_dir = original(config, base=str(tmp_path / "artifacts"))
    common.run_dir_for = lambda cfg: original(cfg, base=str(tmp_path / "artifacts"))
    try:
        main(str(config_path))
        first_results = (run_dir / "results.json").read_bytes()
        main(str(config_path))
        second_results = (run_dir / "results.json").read_bytes()
    finally:
        common.run_dir_for = original

    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    return run_dir, results, first_results, second_results


def test_e5_smoke_manifest_and_determinism(e5_run):
    run_dir, _results, first_results, second_results = e5_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e5_minimal_machine.png",
        "e5_minimal_machine.csv",
        "e5_internalization_witnesses.png",
        "e5_internalization_witnesses.csv",
        "e5_payoff.png",
        "e5_payoff.csv",
        "e5_payoff_v2_ladder.png",
        "e5_payoff_v2_ladder.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e5_n4_and_trap_quotient_diagnostics(e5_run):
    _run_dir, results, _first, _second = e5_run

    assert results["quotients"]["n4_hidden"]["witness_count"] >= 1
    assert results["quotients"]["n4_hidden"]["max_fiber"] == 2
    assert results["protocol_trap"]["naive_witness_count"] == 4
    assert results["protocol_trap"]["internalized_witness_count"] == 4
    assert results["protocol_trap"]["internalized_delta_max"] == "2438/78125"
    assert results["protocol_trap"]["classification"] == "genuine_memory_after_internalization"
    assert all(row["comparison_map_defined"] for row in results["quotients"].values())
    row = results["quotients"]["n4_hidden"]
    assert Fraction(row["uniform_prediction_error_lower_bound"]) == Fraction(row["delta_max"]) / 2


def test_e5_machine_degenerate_and_p52_honest_negative(e5_run):
    _run_dir, results, _first, _second = e5_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert results["minimal_machine"]["degenerate"] is True
    assert predictions["P5.2"]["verdict"] == "registered-negative"
    assert predictions["P5.2"]["grade"] == "registered-negative"
    assert predictions["P5.3"]["verdict"] == "registered-negative"


def test_e5_currentization_mode_bit_singleton(e5_run):
    _run_dir, results, _first, _second = e5_run

    currentization = results["currentization"]["n4_hidden"]
    assert currentization["passing_sets"] == [["mode_bit"]]
    assert currentization["min_cardinality"] == 1
    assert currentization["mode_singleton_passes"] is True
    assert currentization["pure_check_singleton_passes"] is False


def test_e5_payoff_v2_pinned_values():
    point = _payoff_v2_point(
        "frozen_defaults",
        Fraction(1, 50),
        Fraction(1, 50),
        300000,
        0,
        (2, 4, 8, 16),
        (2, 4, 8, 16),
    )

    assert point["scoring_window"] == "heldout_second_half"
    assert point["static_nll"] == pytest.approx(0.372643, abs=1e-6)
    assert point["exact_filter_gap"] == pytest.approx(0.00189933, abs=1e-6)
    assert point["oracle_gap"] == pytest.approx(0.01091055, abs=1e-6)
    assert point["run_length"]["8"]["gap"] == pytest.approx(0.000805, abs=1e-6)


def test_e5_payoff_v2_ladder_shape():
    points = (
        _payoff_v2_point("frozen_defaults", Fraction(1, 50), Fraction(1, 50), 300000, 0, (2, 4, 8, 16), (2, 4, 8, 16)),
        _payoff_v2_point("loud_mode", Fraction(1, 10), Fraction(1, 100), 300000, 0, (2, 4, 8, 16), (2, 4, 8, 16)),
    )

    for point in points:
        assert point["oracle_gap"] > point["exact_filter_gap"] > 0.0
        assert all(row["gap"] > 0.0 for row in point["run_length"].values())
        assert point["run_length"]["8"]["gap"] >= point["run_length"]["2"]["gap"]
    assert all(row["gap"] < 0.0 for row in points[0]["rounding"].values())
    # Fitting on the training prefix and scoring a common held-out window
    # preserves the positive loud-mode K=16 result of the original protocol.
    assert points[1]["rounding"]["16"]["gap"] == pytest.approx(0.028088355247030794, abs=1e-9)


def test_e5_legacy_accuracies_unchanged():
    # Pinned to the committed artifact's payoff.n4_hidden block (not read from a
    # generated results.json, which is gitignored and absent in a clean checkout
    # per .gitignore's "only manifests under artifacts/**" rule). This is a
    # regression check that the _payoff_hidden belief-ordering fix is value-neutral
    # at the frozen N4 defaults, where the belief machine is degenerate.
    expected = {
        "syndrome_only_accuracy": 0.49929,
        "machine_accuracy": 0.49929,
        "memory_only_accuracy": 0.48944,
        "machine_minus_syndrome": 0.0,
        "rounds": 100000,
    }
    n4_noise = n4(Fraction(1, 50), Fraction(1, 50), 3)
    assert n4_noise.hidden is not None
    model = rep3_n4_model(Fraction(1, 50), Fraction(1, 50), exact=True)
    machine = _belief_machine(model, Fraction(1, 50), depth=6, cap=10000, mode_models=n4_noise.hidden.mode_models)
    payoff = _payoff_hidden(model, machine, rounds=100000, seed=1)

    assert payoff == expected


def test_syndrome_likelihood_is_the_marginal_of_the_sensor_actually_read():
    from sbqos.codes import rep_code
    from sbqos.markov import _delta_distribution
    code = rep_code(3)
    model = n4(Fraction(1, 50), Fraction(1, 50), code.n)
    for noise, p in zip(model.hidden.mode_models, (Fraction(1, 50), Fraction(3, 50))):
        delta = _delta_distribution(code.n, code.checks + code.logicals[1:], noise, True)
        # Each depolarizing channel has independent X-content probability u.
        # Each nonzero repetition syndrome has probability u(1-u).
        u = 2 * p / 3
        q = u * (1 - u)
        assert _syndrome_likelihood(delta) == (1 - 3 * q, q, q, q)


def test_bayes_filter_uses_known_initial_mode_and_predicts_before_observing():
    d0 = np.array([0.9, 0.1])
    d1 = np.array([0.2, 0.8])
    result = _payoff_v2_exact_filter(np.array([0, 1]), d0, d1, Fraction(1, 10))
    # Direct enumeration: P(x0=0)=.81+.02=.83. The joint law of
    # (x0=0,x1=1) is .81*(.09+.08)+.02*(.01+.72)=.1523.
    np.testing.assert_allclose(np.exp(-result["losses"]), [0.83, 0.1523 / 0.83], atol=1e-15)
    assert result["beliefs"][0] == pytest.approx(2 / 83)


def test_rounding_prototype_grid_does_not_read_the_heldout_future():
    d0, d1 = _payoff_v2_deltas(Fraction(1, 50))
    mix = (d0 + d1) / 2
    switch = Fraction(1, 50)
    grids = []
    for outcomes in (np.array([0, 0, 2, 3, 0, 0, 0, 0]), np.array([0, 0, 2, 3, 7, 7, 7, 7])):
        filter_result = _payoff_v2_exact_filter(outcomes, d0, d1, switch)
        result = _payoff_v2_rounding_gap(outcomes, d0, d1, mix, switch, filter_result["beliefs"], 4)
        assert result["prototype_fit_window"] == "training_first_half"
        grids.append(result["prototypes"])
    assert grids[0] == grids[1]


def test_minimality_certificate_is_relative_to_the_declared_packaged_machine():
    model = rep3_n4_model(exact=True)
    noise = n4(Fraction(1, 50), Fraction(1, 50), 3)
    machine = _belief_machine(model, Fraction(1, 50), 2, 100, noise.hidden.mode_models)
    certificate = _packaged_machine_minimality(machine)
    assert len(machine.nodes) == 8
    assert certificate["minimal_predictive_state_count"] == certificate["immediate_output_lower_bound"] == 2
    assert len(certificate["reachable_nodes"]) == 4
    assert certificate["reachable_predictive_state_count"] == 1
    assert all(len(group) == 4 for group in certificate["predictive_classes"])
    # The exact predictive readouts differ between the two prototypes, even
    # though the MAP logical decisions used by the legacy payoff coincide.
    for output in certificate["outputs"]:
        assert sum((Fraction(p) for p in output), Fraction(0)) == 1


def test_impossible_observation_does_not_create_a_bayes_posterior():
    likelihoods = [(Fraction(1), Fraction(0), Fraction(0), Fraction(0))] * 2
    with pytest.raises(ValueError, match="zero probability"):
        _posterior(Fraction(0), Fraction(0), likelihoods, 1)


def test_minimization_checks_future_transitions_as_well_as_current_outputs():
    model = rep3_n4_model(exact=True)
    noise = n4(Fraction(1, 50), Fraction(1, 50), 3)
    machine = _belief_machine(model, Fraction(1, 50), 2, 100, noise.hidden.mode_models)
    edges = deepcopy(machine.edges)
    # Two beta=0 nodes have the same immediate prediction but one now reacts
    # differently to symbol 3. They cannot share a predictive machine state.
    edges[0]["3"]["to"] = [3, 1]
    modified = replace(machine, edges=edges)
    assert _packaged_machine_minimality(modified)["minimal_predictive_state_count"] > 2
