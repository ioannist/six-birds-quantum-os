import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e3_check_selection import main


CONFIG_PATH = Path("src/sbqos/configs/e3.json")


@pytest.fixture(scope="module")
def e3_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e3")
    config = load_config(str(CONFIG_PATH))
    config_path = tmp_path / "e3.json"
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


def test_e3_smoke_manifest_and_determinism(e3_run):
    run_dir, _results, first_results, second_results = e3_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e3_coverage_vs_budget.png",
        "e3_coverage_vs_budget.csv",
        "e3_degree_ladder.png",
        "e3_degree_ladder.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e3_spot_values_match_manager_ground_truth(e3_run):
    _run_dir, results, _first, _second = e3_run
    greedy = {row["budget"]: row["trace_xi"] for row in results["surf3_greedy"]["greedy_curve"]}

    assert greedy[1] == pytest.approx(0.356051375371, rel=1e-9)
    assert greedy[8] == pytest.approx(0.17538887995719527, rel=1e-9)

    rung2 = results["rep3_ladder"]["rungs"][1]["trace_xi"]
    assert rung2 == pytest.approx(0.027574927113702623, rel=1e-12)
    assert results["rep3_ladder"]["exact_mmse_fraction"] == "47291/1715000"
    assert results["rep3_ladder"]["rung2_minus_mmse"] == 0.0


def test_e3_surf5_cap_drop_count_is_reported(e3_run):
    _run_dir, results, _first, _second = e3_run
    cap_log = results["surf5_spot"]["cap_log"]

    assert cap_log["dropped_pairs"] > 0
    assert cap_log["total_degree2_pairs"] == cap_log["kept_adjacent_pairs"] + cap_log["dropped_pairs"]
