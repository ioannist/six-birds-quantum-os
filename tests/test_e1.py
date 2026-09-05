import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e1_coverage import main


CONFIG_PATH = Path("src/sbqos/configs/e1.json")


def test_e1_end_to_end_writes_artifacts_and_manifest(tmp_path, monkeypatch):
    run_dir = _patch_run_dir(monkeypatch, tmp_path)

    main(str(CONFIG_PATH))

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "rep5_trace_by_subset_size.png",
        "rep5_trace_by_subset_size.csv",
        "surf3_witness_overlap.png",
        "surf3_witness_overlap.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True


def test_e1_results_are_deterministic(tmp_path, monkeypatch):
    run_dir = _patch_run_dir(monkeypatch, tmp_path)

    main(str(CONFIG_PATH))
    first = (run_dir / "results.json").read_bytes()
    main(str(CONFIG_PATH))
    second = (run_dir / "results.json").read_bytes()

    assert first == second


def test_e1_spot_values_and_honest_registered_negative(tmp_path, monkeypatch):
    run_dir = _patch_run_dir(monkeypatch, tmp_path)

    main(str(CONFIG_PATH))
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))

    assert results["full"]["rep3"]["trace_xi"] == pytest.approx(0.08367977099236641, rel=1e-9)
    assert results["full"]["rep5"]["trace_xi"] == pytest.approx(0.07397290990602258, rel=1e-9)
    assert results["full"]["surf3"]["trace_xi"] == pytest.approx(0.17538887995719527, rel=1e-9)

    predictions = {entry["id"]: entry for entry in results["predictions"]}
    assert predictions["P1.1"]["verdict"] == "registered-negative"
    assert predictions["P1.3"]["verdict"] == "registered-negative"
    assert predictions["P1.2"]["verdict"] == "registered-positive"
    assert predictions["P1.4"]["verdict"] == "registered-positive"
    assert all(entry["grade"] == entry["verdict"] for entry in predictions.values())


def _patch_run_dir(monkeypatch, tmp_path):
    config = load_config(str(CONFIG_PATH))
    original = common.run_dir_for
    run_dir = original(config, base=str(tmp_path))
    monkeypatch.setattr(common, "run_dir_for", lambda cfg: original(cfg, base=str(tmp_path)))
    return run_dir
