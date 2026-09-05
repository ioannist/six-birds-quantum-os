import json
from pathlib import Path

import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import common
from sbqos.experiments.e4_existence import main


CONFIG_PATH = Path("src/sbqos/configs/e4.json")


@pytest.fixture(scope="module")
def e4_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e4")
    config = load_config(str(CONFIG_PATH))
    # The frozen artifact run keeps SURF(3); this unit smoke narrows E4 to
    # REP-family models because SURF(3)'s 1024-state construction is already
    # covered directly in markov/closure tests and by reproduce_all.
    config["models"] = ["rep3_n1", "n4", "n5", "broken"]
    config["taus"] = [1]
    config["n5_horizons"] = [100]
    config["stream_length"] = 200
    config_path = tmp_path / "e4.json"
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


def test_e4_end_to_end_writes_artifacts_manifest_and_is_deterministic(e4_run):
    run_dir, _results, first_results, second_results = e4_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e4_delta_vs_p.png",
        "e4_delta_vs_p.csv",
        "e4_n5_rm_ratio.png",
        "e4_n5_rm_ratio.csv",
        "e4_cd_delta_pred.png",
        "e4_cd_delta_pred.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e4_spot_values_match_manager_derivations(e4_run):
    _run_dir, results, _first, _second = e4_run

    baseline = results["baseline_certificate"]
    assert baseline["status"] == "certified"
    assert baseline["delta"] == pytest.approx(0.007144875, rel=1e-12)
    assert baseline["cd_tau"] == pytest.approx(0.014804630357312679, rel=1e-12)
    assert baseline["multiplicity"] == 2

    broken = results["broken_control"]
    assert broken["status"] == "trivialized"
    assert broken["delta"] == 0.0
    assert broken["multiplicity"] == 1

    n4_tau1 = _row(results["certificate_table"], "n4", 1)
    assert n4_tau1["cd_tau"] == pytest.approx(0.013490507923045155, rel=1e-12)

    n5_h100 = next(row for row in results["n5_horizon_curve"] if row["horizon"] == 100)
    assert n5_h100["route_mismatch"] == pytest.approx(0.3961504575449871, rel=1e-6)
    assert n5_h100["ratio"] == pytest.approx(6.177784912982255, rel=1e-6)


def test_e4_honest_negative_verdicts_are_locked(e4_run):
    _run_dir, results, _first, _second = e4_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert predictions["P4.1"]["verdict"] == "registered-negative"
    assert predictions["P4.3"]["verdict"] == "registered-negative"
    assert all(entry["grade"] == entry["verdict"] for entry in predictions.values())
    assert "excluding N5" in predictions["P4.5"]["interpretation"]


def _row(rows, model, tau):
    return next(row for row in rows if row["model"] == model and row["tau"] == tau)
