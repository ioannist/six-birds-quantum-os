import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e7_witness_ladder import main


CONFIG_PATH = Path("src/sbqos/configs/e7.json")


@pytest.fixture(scope="module")
def e7_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e7")
    config = load_config(str(CONFIG_PATH))
    config["n_grid"] = [250]
    config["n_seeds"] = 1
    config["bootstrap_B"] = 2
    config["null_runs"] = 1
    config["detect_seeds_required"] = 1
    config["baseline_model_shots"] = 1000
    config["cusum_run_length"] = 100
    config["cusum_B"] = 5
    config_path = tmp_path / "e7.json"
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


def test_e7_smoke_manifest_and_determinism(e7_run):
    run_dir, _results, first_results, second_results = e7_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e7_detection_latency.png",
        "e7_detection_latency.csv",
        "e7_naming_overlap.png",
        "e7_naming_overlap.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e7_predictions_present_and_p73_consistent(e7_run):
    _run_dir, results, _first, _second = e7_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert set(predictions) == {"P7.1", "P7.2", "P7.3", "P7.4", "P7.5", "P7.6", "P7.7"}
    for entry in predictions.values():
        assert "verdict" in entry
        assert "values" in entry

    p73 = predictions["P7.3"]
    n_det = p73["values"]["N_det"]
    baseline = n_det["baseline"]
    some_w2_beats = any(
        value is not None and (baseline is None or value < baseline)
        for key, value in n_det.items()
        if key in {"w2a", "w2b", "w2c", "w2d"}
    )
    expected = "registered-negative" if some_w2_beats else "registered-positive"
    assert p73["verdict"] == expected
