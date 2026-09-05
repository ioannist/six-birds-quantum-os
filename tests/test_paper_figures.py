from __future__ import annotations

import csv
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "paper" / "figures" / "make_figures.py"

SOURCE_SPECS = {
    "F3": (Path("e3_default/bfb9ffc6/e3_coverage_vs_budget.csv"), ("budget", "greedy", "lex", "random_mean", "random_min", "random_max")),
    "F4": (Path("e3_default/bfb9ffc6/e3_degree_ladder.csv"), ("rung", "trace_xi", "mmse_floor")),
    "F5": (Path("e5_default/941e4f34/e5_payoff_v2_ladder.csv"), ("point", "predictor", "gap")),
    "F6": (Path("e7_default/ab6885e6/e7_detection_latency.csv"), ("scenario", "N", "w2a", "w2b", "w2d", "baseline", "baseline_cusum")),
    "F7": (Path("e7_default/ab6885e6/e7_naming_overlap.csv"), ("scenario", "modal_qubit", "named_in_pair_count", "mean_overlap")),
    "F8": (Path("e8_default/cf7094d8/e8_detection_latency.csv"), ("N", "witness_frac", "baseline_frac")),
    "F9": (Path("e9_default/f24323a0/e9_post_drift_error.csv"), ("policy", "mean_post_drift_error", "mean_recalibration_events")),
}

EXPECTED_STEMS = (
    "fig_F3_e3_coverage_vs_budget", "fig_F4_e3_degree_ladder", "fig_F5_e5_payoff_ladder",
    "fig_F6_e7_detection_ladder", "fig_F7_e7_naming_overlap", "fig_F8_e8_circuit_level",
    "fig_F9_e9_closed_loop",
)

# Every fixture is intentionally out of canonical order. Values are literal and
# distinct enough that swapped rows or series cannot pass the artist checks.
F3_ROWS = [
    {"budget": "8", "greedy": "0.18", "lex": "0.19", "random_mean": "0.185", "random_min": "0.17", "random_max": "0.20"},
    {"budget": "2", "greedy": "0.36", "lex": "0.38", "random_mean": "0.385", "random_min": "0.35", "random_max": "0.42"},
    {"budget": "6", "greedy": "0.23", "lex": "0.25", "random_mean": "0.27", "random_min": "0.22", "random_max": "0.30"},
    {"budget": "0", "greedy": "0.44", "lex": "0.43", "random_mean": "0.42", "random_min": "0.39", "random_max": "0.445"},
    {"budget": "4", "greedy": "0.29", "lex": "0.31", "random_mean": "0.34", "random_min": "0.28", "random_max": "0.37"},
    {"budget": "1", "greedy": "0.40", "lex": "0.41", "random_mean": "0.405", "random_min": "0.38", "random_max": "0.43"},
    {"budget": "7", "greedy": "0.20", "lex": "0.22", "random_mean": "0.235", "random_min": "0.19", "random_max": "0.26"},
    {"budget": "3", "greedy": "0.32", "lex": "0.35", "random_mean": "0.36", "random_min": "0.31", "random_max": "0.40"},
    {"budget": "5", "greedy": "0.26", "lex": "0.28", "random_mean": "0.30", "random_min": "0.25", "random_max": "0.33"},
]
F4_ROWS = [
    {"rung": "2", "trace_xi": "0.027574927113702623", "mmse_floor": "0.027574927113702623"},
    {"rung": "1", "trace_xi": "0.08367977099236641", "mmse_floor": "0.027574927113702623"},
]
F5_ROWS = [
    {"point": "loud_mode", "predictor": "run_length_K8", "gap": "0.0105"},
    {"point": "frozen_defaults", "predictor": "static", "gap": "0.0"},
    {"point": "loud_mode", "predictor": "oracle", "gap": "0.0583"},
    {"point": "frozen_defaults", "predictor": "run_length_K4", "gap": "0.0004"},
    {"point": "loud_mode", "predictor": "static", "gap": "0.0"},
    {"point": "frozen_defaults", "predictor": "rounding_K16", "gap": "-0.0037"},
    {"point": "loud_mode", "predictor": "exact_filter", "gap": "0.0361"},
    {"point": "frozen_defaults", "predictor": "oracle", "gap": "0.0106"},
    {"point": "loud_mode", "predictor": "run_length_K2", "gap": "0.0042"},
    {"point": "frozen_defaults", "predictor": "exact_filter", "gap": "0.0019"},
    {"point": "loud_mode", "predictor": "rounding_K2", "gap": "-0.0703"},
    {"point": "frozen_defaults", "predictor": "run_length_K2", "gap": "0.0001"},
    {"point": "loud_mode", "predictor": "run_length_K16", "gap": "0.0103"},
    {"point": "frozen_defaults", "predictor": "rounding_K4", "gap": "-0.0061"},
    {"point": "loud_mode", "predictor": "rounding_K16", "gap": "0.0301"},
    {"point": "frozen_defaults", "predictor": "run_length_K8", "gap": "0.0008"},
    {"point": "loud_mode", "predictor": "rounding_K4", "gap": "-0.0444"},
    {"point": "frozen_defaults", "predictor": "rounding_K2", "gap": "-0.0047"},
    {"point": "loud_mode", "predictor": "run_length_K4", "gap": "0.0088"},
    {"point": "frozen_defaults", "predictor": "run_length_K16", "gap": "0.0009"},
    {"point": "loud_mode", "predictor": "rounding_K8", "gap": "-0.0375"},
    {"point": "frozen_defaults", "predictor": "rounding_K8", "gap": "-0.0052"},
]
F6_ROWS = [
    {"scenario": "4_8", "N": "1000", "w2a": "0.39", "w2b": "0.49", "w2d": "0.59", "baseline": "0.69", "baseline_cusum": "0.79"},
    {"scenario": "0_3", "N": "4000", "w2a": "0.74", "w2b": "0.74", "w2d": "0.84", "baseline": "0.94", "baseline_cusum": "0.94"},
    {"scenario": "2_5", "N": "250", "w2a": "0.14", "w2b": "0.24", "w2d": "0.34", "baseline": "0.44", "baseline_cusum": "0.54"},
    {"scenario": "0_3", "N": "250", "w2a": "0.10", "w2b": "0.10", "w2d": "0.20", "baseline": "0.20", "baseline_cusum": "0.30"},
    {"scenario": "4_8", "N": "4000", "w2a": "0.75", "w2b": "0.85", "w2d": "0.85", "baseline": "0.95", "baseline_cusum": "0.95"},
    {"scenario": "2_5", "N": "1000", "w2a": "0.36", "w2b": "0.46", "w2d": "0.56", "baseline": "0.66", "baseline_cusum": "0.76"},
    {"scenario": "0_3", "N": "1000", "w2a": "0.22", "w2b": "0.32", "w2d": "0.42", "baseline": "0.52", "baseline_cusum": "0.62"},
    {"scenario": "4_8", "N": "250", "w2a": "0.17", "w2b": "0.27", "w2d": "0.37", "baseline": "0.47", "baseline_cusum": "0.57"},
    {"scenario": "2_5", "N": "4000", "w2a": "0.78", "w2b": "0.88", "w2d": "0.88", "baseline": "0.98", "baseline_cusum": "0.98"},
    {"scenario": "0_3", "N": "16000", "w2a": "0.90", "w2b": "0.91", "w2d": "0.92", "baseline": "0.93", "baseline_cusum": "0.94"},
    {"scenario": "2_5", "N": "500", "w2a": "0.15", "w2b": "0.25", "w2d": "0.35", "baseline": "0.45", "baseline_cusum": "0.55"},
    {"scenario": "4_8", "N": "8000", "w2a": "0.82", "w2b": "0.83", "w2d": "0.84", "baseline": "0.85", "baseline_cusum": "0.86"},
    {"scenario": "0_3", "N": "500", "w2a": "0.11", "w2b": "0.21", "w2d": "0.31", "baseline": "0.41", "baseline_cusum": "0.51"},
    {"scenario": "2_5", "N": "16000", "w2a": "0.91", "w2b": "0.92", "w2d": "0.93", "baseline": "0.94", "baseline_cusum": "0.95"},
    {"scenario": "4_8", "N": "2000", "w2a": "0.50", "w2b": "0.60", "w2d": "0.70", "baseline": "0.80", "baseline_cusum": "0.90"},
    {"scenario": "0_3", "N": "8000", "w2a": "0.85", "w2b": "0.86", "w2d": "0.87", "baseline": "0.88", "baseline_cusum": "0.89"},
    {"scenario": "2_5", "N": "2000", "w2a": "0.47", "w2b": "0.57", "w2d": "0.67", "baseline": "0.77", "baseline_cusum": "0.87"},
    {"scenario": "4_8", "N": "500", "w2a": "0.18", "w2b": "0.28", "w2d": "0.38", "baseline": "0.48", "baseline_cusum": "0.58"},
    {"scenario": "0_3", "N": "2000", "w2a": "0.33", "w2b": "0.43", "w2d": "0.53", "baseline": "0.63", "baseline_cusum": "0.73"},
    {"scenario": "2_5", "N": "8000", "w2a": "0.81", "w2b": "0.82", "w2d": "0.83", "baseline": "0.84", "baseline_cusum": "0.85"},
    {"scenario": "4_8", "N": "16000", "w2a": "0.92", "w2b": "0.93", "w2d": "0.94", "baseline": "0.95", "baseline_cusum": "0.96"},
]
F7_ROWS = [
    {"scenario": "4_8", "modal_qubit": "5", "named_in_pair_count": "9", "mean_overlap": "0.87"},
    {"scenario": "0_3", "modal_qubit": "7", "named_in_pair_count": "1", "mean_overlap": "0.12"},
    {"scenario": "2_5", "modal_qubit": "8", "named_in_pair_count": "4", "mean_overlap": "0.45"},
]
F8_ROWS = [
    {"N": "100", "witness_frac": "0.66", "baseline_frac": "0.39"},
    {"N": "10", "witness_frac": "0.11", "baseline_frac": "0.05"},
    {"N": "1000", "witness_frac": "0.95", "baseline_frac": "0.85"},
    {"N": "50", "witness_frac": "0.44", "baseline_frac": "0.24"},
    {"N": "2000", "witness_frac": "0.99", "baseline_frac": "0.97"},
    {"N": "20", "witness_frac": "0.22", "baseline_frac": "0.12"},
    {"N": "500", "witness_frac": "0.86", "baseline_frac": "0.72"},
    {"N": "250", "witness_frac": "0.77", "baseline_frac": "0.58"},
]
F9_ROWS = [
    {"policy": "oracle", "mean_post_drift_error": "0.091", "mean_recalibration_events": "0.0"},
    {"policy": "scheduled_frequent", "mean_post_drift_error": "0.102", "mean_recalibration_events": "8.0"},
    {"policy": "static", "mean_post_drift_error": "0.121", "mean_recalibration_events": "0.0"},
    {"policy": "witness", "mean_post_drift_error": "0.094", "mean_recalibration_events": "1.5"},
    {"policy": "scheduled_matched", "mean_post_drift_error": "0.112", "mean_recalibration_events": "1.6"},
]

FIXTURE_ROWS = {"F3": F3_ROWS, "F4": F4_ROWS, "F5": F5_ROWS, "F6": F6_ROWS, "F7": F7_ROWS, "F8": F8_ROWS, "F9": F9_ROWS}

_SPEC = importlib.util.spec_from_file_location("paper_make_figures", SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
make_figures = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(make_figures)


def _bar_mapping(ax, bars) -> list[tuple[str, float]]:
    tick_positions = np.asarray(ax.get_xticks(), dtype=float)
    tick_labels = [tick.get_text() for tick in ax.get_xticklabels()]
    result = []
    for bar in bars:
        center = bar.get_x() + bar.get_width() / 2
        index = int(np.argmin(np.abs(tick_positions - center)))
        result.append((tick_labels[index], bar.get_height()))
    return result


def test_artist_data_fidelity_and_order():
    figures = []
    try:
        figure = make_figures.fig_F3(F3_ROWS)
        figures.append(figure)
        ax = figure.axes[0]
        lines = {line.get_label(): line for line in ax.lines}
        expected_f3 = {
            "greedy (chain rule)": [0.44, 0.40, 0.36, 0.32, 0.29, 0.26, 0.23, 0.20, 0.18],
            "lexicographic": [0.43, 0.41, 0.38, 0.35, 0.31, 0.28, 0.25, 0.22, 0.19],
            "random (mean of 10 seeds)": [0.42, 0.405, 0.385, 0.36, 0.34, 0.30, 0.27, 0.235, 0.185],
        }
        for label, values in expected_f3.items():
            np.testing.assert_array_equal(lines[label].get_xdata(), list(range(9)))
            np.testing.assert_array_equal(lines[label].get_ydata(), values)
        vertices = ax.collections[0].get_paths()[0].vertices
        expected_min = [0.39, 0.38, 0.35, 0.31, 0.28, 0.25, 0.22, 0.19, 0.17]
        expected_max = [0.445, 0.43, 0.42, 0.40, 0.37, 0.33, 0.30, 0.26, 0.20]
        for budget, lower, upper in zip(range(9), expected_min, expected_max, strict=True):
            for point in ((budget, lower), (budget, upper)):
                assert np.any(np.all(np.isclose(vertices, point), axis=1))

        figure = make_figures.fig_F4(F4_ROWS)
        figures.append(figure)
        assert _bar_mapping(figure.axes[0], figure.axes[0].patches) == [
            ("degree-1", 0.08367977099236641), ("degree-2-complete", 0.027574927113702623),
        ]

        figure = make_figures.fig_F5(F5_ROWS)
        figures.append(figure)
        f5_labels = (
            "oracle", "exact filter", "run-length K=2", "run-length K=4", "run-length K=8",
            "run-length K=16", "rounding K=2", "rounding K=4", "rounding K=8", "rounding K=16",
        )
        expected_f5 = (
            (0.0106, 0.0019, 0.0001, 0.0004, 0.0008, 0.0009, -0.0047, -0.0061, -0.0052, -0.0037),
            (0.0583, 0.0361, 0.0042, 0.0088, 0.0105, 0.0103, -0.0703, -0.0444, -0.0375, 0.0301),
        )
        for ax, values in zip(figure.axes, expected_f5, strict=True):
            mapping = _bar_mapping(ax, ax.patches)
            assert len(mapping) == 10
            assert [label for label, _height in mapping] == list(f5_labels)
            np.testing.assert_array_equal([height for _label, height in mapping], values)

        figure = make_figures.fig_F6(F6_ROWS)
        figures.append(figure)
        f6_labels = (
            ("w2a", "W2a: legacy statistic, recalibrated null"),
            ("w2b", "W2b: quadratic statistic (W2c naming shares this curve)"),
            ("w2d", "W2d: sequential (CUSUM)"),
            ("baseline", "baseline"),
            ("baseline_cusum", "baseline CUSUM"),
        )
        expected_f6 = {
            "0_3": {
                "w2a": [0.10, 0.11, 0.22, 0.33, 0.74, 0.85, 0.90],
                "w2b": [0.10, 0.21, 0.32, 0.43, 0.74, 0.86, 0.91],
                "w2d": [0.20, 0.31, 0.42, 0.53, 0.84, 0.87, 0.92],
                "baseline": [0.20, 0.41, 0.52, 0.63, 0.94, 0.88, 0.93],
                "baseline_cusum": [0.30, 0.51, 0.62, 0.73, 0.94, 0.89, 0.94],
            },
            "2_5": {
                "w2a": [0.14, 0.15, 0.36, 0.47, 0.78, 0.81, 0.91],
                "w2b": [0.24, 0.25, 0.46, 0.57, 0.88, 0.82, 0.92],
                "w2d": [0.34, 0.35, 0.56, 0.67, 0.88, 0.83, 0.93],
                "baseline": [0.44, 0.45, 0.66, 0.77, 0.98, 0.84, 0.94],
                "baseline_cusum": [0.54, 0.55, 0.76, 0.87, 0.98, 0.85, 0.95],
            },
            "4_8": {
                "w2a": [0.17, 0.18, 0.39, 0.50, 0.75, 0.82, 0.92],
                "w2b": [0.27, 0.28, 0.49, 0.60, 0.85, 0.83, 0.93],
                "w2d": [0.37, 0.38, 0.59, 0.70, 0.85, 0.84, 0.94],
                "baseline": [0.47, 0.48, 0.69, 0.80, 0.95, 0.85, 0.95],
                "baseline_cusum": [0.57, 0.58, 0.79, 0.90, 0.95, 0.86, 0.96],
            },
        }
        for ax, scenario in zip(figure.axes, ("0_3", "2_5", "4_8"), strict=True):
            lines = {line.get_label(): line for line in ax.lines}
            for key, label in f6_labels:
                np.testing.assert_array_equal(
                    lines[label].get_xdata(), [250, 500, 1000, 2000, 4000, 8000, 16000]
                )
                rendered = np.asarray(lines[label].get_ydata(), dtype=float)
                source = np.asarray(expected_f6[scenario][key], dtype=float)
                np.testing.assert_allclose(rendered, source, atol=0.0125, rtol=0.0)
                assert np.max(np.abs(rendered - source)) <= 0.012 + 1e-12

        figure = make_figures.fig_F7(F7_ROWS)
        figures.append(figure)
        ax = figure.axes[0]
        assert [text.get_text() for text in ax.get_legend().get_texts()] == [
            "mean logical-direction overlap", "seeds naming a true-pair qubit / 10",
            "registered overlap bar (0.6)", "registered naming bar (8/10)",
        ]
        assert [tick.get_text() for tick in ax.get_xticklabels()] == ["(0,3)", "(2,5)", "(4,8)"]
        assert len(ax.containers[0]) == len(ax.containers[1]) == 3
        assert _bar_mapping(ax, ax.containers[0]) == [
            ("(0,3)", 0.12), ("(2,5)", 0.45), ("(4,8)", 0.87),
        ]
        assert _bar_mapping(ax, ax.containers[1]) == [
            ("(0,3)", 0.1), ("(2,5)", 0.4), ("(4,8)", 0.9),
        ]

        figure = make_figures.fig_F8(F8_ROWS)
        figures.append(figure)
        lines = {line.get_label(): line for line in figure.axes[0].lines}
        for label, values in (
            ("corrected witness (W2b)", [0.11, 0.22, 0.44, 0.66, 0.77, 0.86, 0.95, 0.99]),
            ("pymatching baseline", [0.05, 0.12, 0.24, 0.39, 0.58, 0.72, 0.85, 0.97]),
        ):
            np.testing.assert_array_equal(lines[label].get_xdata(), [10, 20, 50, 100, 250, 500, 1000, 2000])
            np.testing.assert_array_equal(lines[label].get_ydata(), values)

        figure = make_figures.fig_F9(F9_ROWS)
        figures.append(figure)
        mapping = _bar_mapping(figure.axes[0], figure.axes[0].patches)
        assert len(mapping) == 5
        assert mapping == [
            ("static", 0.121), ("scheduled\n(budget-matched)", 0.112),
            ("scheduled\n(frequent)", 0.102), ("witness-\ntriggered", 0.094), ("oracle", 0.091),
        ]
    finally:
        for figure in figures:
            plt.close(figure)


@pytest.mark.parametrize(
    ("figure_id", "builder", "rows", "domain_field", "unexpected_value"),
    (
        ("F3", make_figures.fig_F3, F3_ROWS, "budget", "99"),
        ("F5", make_figures.fig_F5, F5_ROWS, "predictor", "unexpected"),
        ("F6", make_figures.fig_F6, F6_ROWS, "scenario", "unexpected"),
        ("F8", make_figures.fig_F8, F8_ROWS, "N", "4000"),
        ("F9", make_figures.fig_F9, F9_ROWS, "policy", "unexpected"),
    ),
)
@pytest.mark.parametrize("mutation", ("dropped", "duplicated", "unexpected"))
def test_domain_validation(figure_id, builder, rows, domain_field, unexpected_value, mutation):
    malformed = [dict(row) for row in rows]
    if mutation == "dropped":
        malformed.pop()
    elif mutation == "duplicated":
        malformed.append(dict(malformed[0]))
    else:
        malformed[0][domain_field] = unexpected_value
    with pytest.raises(ValueError, match=figure_id):
        builder(malformed)


@pytest.mark.parametrize("mutation", ("synchronized_drop", "synchronized_unexpected"))
def test_f6_synchronized_grid_validation(mutation):
    malformed = [dict(row) for row in F6_ROWS]
    if mutation == "synchronized_drop":
        malformed = [row for row in malformed if row["N"] != "16000"]
    else:
        malformed.extend(
            [
                {"scenario": "0_3", "N": "32000", "w2a": "0.1", "w2b": "0.2", "w2d": "0.3", "baseline": "0.4", "baseline_cusum": "0.5"},
                {"scenario": "2_5", "N": "32000", "w2a": "0.2", "w2b": "0.3", "w2d": "0.4", "baseline": "0.5", "baseline_cusum": "0.6"},
                {"scenario": "4_8", "N": "32000", "w2a": "0.3", "w2b": "0.4", "w2d": "0.5", "baseline": "0.6", "baseline_cusum": "0.7"},
            ]
        )
    with pytest.raises(ValueError, match="F6"):
        make_figures.fig_F6(malformed)


def test_load_csv_failure_modes(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError) as exc_info:
        make_figures.load_csv(missing, ("a", "b"))
    assert str(missing) in str(exc_info.value)
    assert ".venv/bin/python -m sbqos.reproduce_all" in str(exc_info.value)
    wrong_header = tmp_path / "wrong.csv"
    wrong_header.write_text("wrong,columns\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected CSV header"):
        make_figures.load_csv(wrong_header, ("a", "b"))


def test_fixture_csvs_two_process_determinism(tmp_path):
    artifacts = tmp_path / "artifacts"
    _write_fixture_csvs(artifacts)
    _assert_two_process_determinism(artifacts, tmp_path / "fixture-runs")


def test_real_artifacts_two_process_determinism(tmp_path):
    artifacts = REPO_ROOT / "artifacts"
    missing = [artifacts / relative for relative, _header in SOURCE_SPECS.values() if not (artifacts / relative).is_file()]
    if missing:
        pytest.skip("paper source CSVs are absent; regenerate with `.venv/bin/python -m sbqos.reproduce_all`")
    _assert_two_process_determinism(artifacts, tmp_path / "real-runs")


def _write_fixture_csvs(artifacts: Path) -> None:
    for figure_id, (relative, header) in SOURCE_SPECS.items():
        path = artifacts / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerows(FIXTURE_ROWS[figure_id])


def _assert_two_process_determinism(artifacts: Path, root: Path) -> None:
    outputs = (root / "output-one", root / "output-two")
    results = []
    for index, output in enumerate(outputs, start=1):
        env = os.environ.copy()
        config_dir = root / f"mplconfig-{index}"
        env["MPLCONFIGDIR"] = str(config_dir)
        results.append(subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--artifacts", str(artifacts), "--out", str(output)],
            check=True, capture_output=True, text=True, env=env,
        ))
    expected = {f"{stem}.{suffix}" for stem in EXPECTED_STEMS for suffix in ("pdf", "png")}
    for output, result, index in zip(outputs, results, (1, 2), strict=True):
        assert {path.name for path in output.iterdir()} == expected
        assert "environment:\n" in result.stdout
        assert f"MPLCONFIGDIR={(root / f'mplconfig-{index}').resolve()}" in result.stdout
        assert "  matplotlib " in result.stdout
        assert "  pillow " in result.stdout
        assert "  fonts: " in result.stdout
    for filename in expected:
        first = outputs[0] / filename
        second = outputs[1] / filename
        assert first.stat().st_size > 0
        assert second.stat().st_size > 0
        assert first.read_bytes() == second.read_bytes(), filename
