import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e6_slack import main


CONFIG_PATH = Path("src/sbqos/configs/e6.json")


@pytest.fixture(scope="module")
def e6_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e6")
    config = load_config(str(CONFIG_PATH))
    config["consequence_shots"] = 20000
    config["n_proxy_seeds"] = 3
    config_path = tmp_path / "e6.json"
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


def test_e6_smoke_manifest_and_determinism(e6_run):
    run_dir, _results, first_results, second_results = e6_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e6_rep5_value_lambda.png",
        "e6_rep5_value_lambda.csv",
        "e6_proxy_costs.png",
        "e6_proxy_costs.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e6_exact_value_curve_and_slack_spots(e6_run):
    _run_dir, results, _first, _second = e6_run

    assert results["rep5"]["V_exact"][4] == pytest.approx(0.1624250729, abs=1e-8)
    assert results["rep5"]["V_exact"][16] == pytest.approx(0.1653247504, abs=1e-8)
    assert results["rep5"]["lambda_exact"][15] == pytest.approx(1.73797e-5, abs=1e-8)
    assert results["rep5"]["slack_point"] == 16


def test_e6_honest_negative_verdicts_for_p61_p62(e6_run):
    _run_dir, results, _first, _second = e6_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert predictions["P6.1"]["verdict"] == "registered-negative"
    assert predictions["P6.2"]["verdict"] == "registered-negative"
    assert all(entry["grade"] == entry["verdict"] for entry in predictions.values())
