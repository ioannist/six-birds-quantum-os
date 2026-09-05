import json
from pathlib import Path
from fractions import Fraction

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e5_decoder_memory import (
    _belief_machine,
    _payoff_hidden,
    _payoff_v2_point,
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

    assert point["static_nll"] == pytest.approx(0.369269, abs=1e-6)
    assert point["exact_filter_gap"] == pytest.approx(0.001956, abs=1e-6)
    assert point["oracle_gap"] == pytest.approx(0.010611, abs=1e-6)
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
    # The specified rounding construction gives a positive K=16 gap on the loud
    # point; keep that observed post-registration measurement pinned instead of
    # tuning the grid to satisfy the expected negative control.
    assert points[1]["rounding"]["16"]["gap"] == pytest.approx(0.0301348888, abs=1e-9)


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
