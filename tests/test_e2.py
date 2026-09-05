import json
from pathlib import Path
from fractions import Fraction
from types import MappingProxyType

import numpy as np
import pytest

from sbqos.artifacts import load_config, verify_manifest
from sbqos.codes import Code, surface_code
from sbqos.experiments import common
from sbqos.experiments.e2_drift_witness import _MatchingAdapter, main
from sbqos.noise import n2


CONFIG_PATH = Path("src/sbqos/configs/e2.json")


@pytest.fixture(scope="module")
def e2_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e2")
    config = load_config(str(CONFIG_PATH))
    config["n_grid"] = [250, 1000]
    config["n_seeds"] = 1
    config["bootstrap_B"] = 2
    config["null_runs"] = 0
    config["baseline_model_shots"] = 1000
    config["n5_window_shots"] = 100
    config["n5_windows"] = 2
    config["detect_seeds_required"] = 1
    config_path = tmp_path / "e2.json"
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


def test_e2_smoke_manifest_and_determinism(e2_run):
    run_dir, _results, first_results, second_results = e2_run

    expected = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "e2_detection_latency.png",
        "e2_detection_latency.csv",
        "e2_witness_directions.png",
        "e2_witness_directions.csv",
        "e2_n5_drift_trace.png",
        "e2_n5_drift_trace.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected
    assert verify_manifest(run_dir) is True
    assert first_results == second_results


def test_e2_analytic_w1_direction_matches_manager_value(e2_run):
    _run_dir, results, _first, _second = e2_run

    assert results["analytic_directions"]["w1"]["abs"][0] == pytest.approx(0.99994, abs=1e-4)
    assert results["analytic_directions"]["w1"]["abs"][1] == pytest.approx(0.01104, abs=1e-4)


def test_e2_prediction_block_normalized(e2_run):
    _run_dir, results, _first, _second = e2_run
    predictions = {entry["id"]: entry for entry in results["predictions"]}

    assert set(predictions) == {"P2.1", "P2.2", "P2.3", "P2.4"}
    for entry in predictions.values():
        assert entry["grade"] == entry["verdict"]
        assert entry["grade"] in {"registered-positive", "registered-negative"}
        assert "values" in entry


def test_e2_layout_assert():
    code = surface_code(3)
    bad_check = np.zeros(2 * code.n, dtype=np.uint8)
    bad_check[0] = 1
    fake = Code(
        name="BAD_SURF3",
        n=code.n,
        k=code.k,
        checks=(bad_check,) + code.checks[1:],
        logicals=code.logicals,
        meta=MappingProxyType({}),
    )

    with pytest.raises(ValueError, match="checks\\[:4\\] are Z-type"):
        _MatchingAdapter(fake, n2(Fraction(3, 100), fake.n))
