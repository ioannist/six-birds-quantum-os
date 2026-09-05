import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e9_control_loop import main


CONFIG_PATH = Path("src/sbqos/configs/e9.json")


@pytest.fixture(scope="module")
def e9_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e9")
    config = load_config(str(CONFIG_PATH))
    config["rounds"] = 3
    config["E_total"] = 3
    config["drift_epoch"] = 1
    config["shots_per_epoch"] = 10
    config["n_seeds"] = 1
    config["N_cal"] = 200
    config["bootstrap_B"] = 2
    config["N_curve"] = 200
    config["candidate_multipliers"] = [1, 20]
    config["schedule_K_matched"] = 2
    config["schedule_K_frequent"] = 1
    config_path = tmp_path / "e9.json"
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


def test_e9_smoke_manifest_and_determinism(e9_run):
    run_dir, _results, first_results, second_results = e9_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e9_post_drift_error.png",
        "e9_post_drift_error.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e9_predictions_present_with_verdicts(e9_run):
    _run_dir, results, _first, _second = e9_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert set(predictions) == {"P9.1", "P9.2", "P9.3", "P9.4"}
    for entry in predictions.values():
        assert "verdict" in entry
        assert "values" in entry
