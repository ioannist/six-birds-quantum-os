import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e8_circuit_level import main


CONFIG_PATH = Path("src/sbqos/configs/e8.json")


@pytest.fixture(scope="module")
def e8_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e8")
    config = load_config(str(CONFIG_PATH))
    config["n_grid"] = [10]
    config["n_seeds"] = 1
    config["detect_seeds_required"] = 1
    config["bootstrap_B"] = 2
    config["null_runs"] = 1
    config["N_cal"] = 3000
    config["baseline_calibration_shots"] = 3000
    config_path = tmp_path / "e8.json"
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


def test_e8_smoke_manifest_and_determinism(e8_run):
    run_dir, _results, first_results, second_results = e8_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e8_detection_latency.png",
        "e8_detection_latency.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e8_predictions_present_with_verdicts(e8_run):
    _run_dir, results, _first, _second = e8_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert set(predictions) == {"P8.1", "P8.2", "P8.cost"}
    for entry in predictions.values():
        assert "verdict" in entry
        assert "values" in entry
