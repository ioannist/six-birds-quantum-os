from fractions import Fraction
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sbqos.artifacts import Run, load_config, parse_fraction, verify_manifest
from sbqos.experiments.common import run_dir_for


def test_load_config_round_trip_unknown_key_rejection_and_parse_fraction(tmp_path):
    path = tmp_path / "e1.json"
    payload = {
        "experiment": "e1",
        "seed": 0,
        "rep3_p": "1/20",
        "rep5_p": "1/20",
        "surf3_p": "3/100",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert load_config(str(path)) == payload
    assert parse_fraction("1/20") == Fraction(1, 20)

    bad_path = tmp_path / "bad.json"
    bad = dict(payload)
    bad["drift"] = True
    bad_path.write_text(json.dumps(bad), encoding="utf-8")

    try:
        load_config(str(bad_path))
    except ValueError as exc:
        assert "unknown config key: drift" in str(exc)
    else:
        raise AssertionError("unknown config key was not rejected")


def test_run_writes_artifacts_manifest_and_detects_corruption(tmp_path):
    config = _e1_config()
    run_dir = tmp_path / "run"

    with Run(config, run_dir) as run:
        run.write_result({"claim_grade": "unit", "value": 0.25})
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        run.save_figure(fig, "fig", [[0, 0], [1, 1]], ["x", "y"])
        plt.close(fig)

    expected_files = {
        "config.json",
        "results.json",
        "environment.json",
        "manifest.json",
        "fig.png",
        "fig.csv",
    }
    assert {p.name for p in run_dir.iterdir()} == expected_files

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest) == {"config.json", "results.json", "fig.png", "fig.csv"}
    assert verify_manifest(run_dir) is True

    with (run_dir / "results.json").open("ab") as f:
        f.write(b"\n")
    assert verify_manifest(run_dir) is False


def test_run_deterministic_json_and_manifest_entries_for_nonfigure_artifacts(tmp_path):
    config = _e1_config()
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"

    _write_same_run(config, run1)
    _write_same_run(dict(reversed(list(config.items()))), run2)

    assert (run1 / "results.json").read_bytes() == (run2 / "results.json").read_bytes()
    assert (run1 / "fig.csv").read_bytes() == (run2 / "fig.csv").read_bytes()

    manifest1 = json.loads((run1 / "manifest.json").read_text(encoding="utf-8"))
    manifest2 = json.loads((run2 / "manifest.json").read_text(encoding="utf-8"))
    assert manifest1["config.json"] == manifest2["config.json"]
    assert manifest1["results.json"] == manifest2["results.json"]
    # PNG bytes can vary across Matplotlib invocations; the paired CSV is the
    # deterministic plotted-data artifact.
    assert manifest1["fig.csv"] == manifest2["fig.csv"]


def test_run_dir_for_uses_sorted_config_hash_independent_of_insertion_order():
    config = _e1_config()
    reordered = dict(reversed(list(config.items())))

    assert run_dir_for(config, base="artifact-root") == run_dir_for(reordered, base="artifact-root")


def _write_same_run(config: dict, run_dir) -> None:
    with Run(config, run_dir) as run:
        run.write_result({"b": 2.0, "a": 1.0})
        fig, ax = plt.subplots()
        ax.plot([0, 1], [1, 0])
        run.save_figure(fig, "fig", [[0, 1], [1, 0]], ["x", "y"])
        plt.close(fig)


def _e1_config() -> dict:
    return {
        "experiment": "e1",
        "seed": 0,
        "rep3_p": "1/20",
        "rep5_p": "1/20",
        "surf3_p": "3/100",
    }
