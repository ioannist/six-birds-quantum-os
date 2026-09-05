#!/usr/bin/env python3
"""Regenerate paper data figures F3-F9 from frozen experiment CSVs."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from importlib.metadata import PackageNotFoundError, version
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "sbqos-matplotlib"))

import matplotlib

matplotlib.use("Agg")

from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np


logging.getLogger("fontTools").setLevel(logging.ERROR)


BLACK = "#000000"
ORANGE = "#E69F00"
SKY_BLUE = "#56B4E9"
GREEN = "#009E73"
YELLOW = "#F0E442"
BLUE = "#0072B2"
VERMILION = "#D55E00"
PURPLE = "#CC79A7"
GREY = "#BBBBBB"

FIGURE_FILES = {
    "F3": "fig_F3_e3_coverage_vs_budget",
    "F4": "fig_F4_e3_degree_ladder",
    "F5": "fig_F5_e5_payoff_ladder",
    "F6": "fig_F6_e7_detection_ladder",
    "F7": "fig_F7_e7_naming_overlap",
    "F8": "fig_F8_e8_circuit_level",
    "F9": "fig_F9_e9_closed_loop",
}

SOURCE_SPECS = {
    "F3": (
        Path("e3_default/bfb9ffc6/e3_coverage_vs_budget.csv"),
        ("budget", "greedy", "lex", "random_mean", "random_min", "random_max"),
    ),
    "F4": (
        Path("e3_default/bfb9ffc6/e3_degree_ladder.csv"),
        ("rung", "trace_xi", "mmse_floor"),
    ),
    "F5": (
        Path("e5_default/941e4f34/e5_payoff_v2_ladder.csv"),
        ("point", "predictor", "gap"),
    ),
    "F6": (
        Path("e7_default/ab6885e6/e7_detection_latency.csv"),
        ("scenario", "N", "w2a", "w2b", "w2d", "baseline", "baseline_cusum"),
    ),
    "F7": (
        Path("e7_default/ab6885e6/e7_naming_overlap.csv"),
        ("scenario", "modal_qubit", "named_in_pair_count", "mean_overlap"),
    ),
    "F8": (
        Path("e8_default/cf7094d8/e8_detection_latency.csv"),
        ("N", "witness_frac", "baseline_frac"),
    ),
    "F9": (
        Path("e9_default/f24323a0/e9_post_drift_error.csv"),
        ("policy", "mean_post_drift_error", "mean_recalibration_events"),
    ),
}

PDF_METADATA = {
    "CreationDate": None,
    "ModDate": None,
    "Creator": None,
    "Producer": None,
}
PNG_METADATA = {"Software": None}

_F3_BUDGETS = tuple(range(9))
_F6_N_GRID = (250, 500, 1000, 2000, 4000, 8000, 16000)
_F8_N_GRID = (10, 20, 50, 100, 250, 500, 1000, 2000)

_FONT_WARNING_EMITTED = False


def _register_latin_modern() -> list[Path]:
    global _FONT_WARNING_EMITTED

    directories: list[Path] = []
    configured = os.environ.get("SBQOS_LM_FONT_DIR")
    if configured:
        directories.append(Path(configured))

    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich:
        result = subprocess.run(
            [kpsewhich, "lmroman10-regular.otf"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            directories.append(Path(result.stdout.strip()).parent)

    font_paths: list[Path] = []
    for directory in directories:
        if directory.is_dir():
            font_paths.extend(sorted(directory.glob("lmroman10-*.otf")))

    resolved_paths = list(dict.fromkeys(font_path.resolve() for font_path in font_paths))
    for font_path in resolved_paths:
        font_manager.fontManager.addfont(font_path)

    if not resolved_paths and not _FONT_WARNING_EMITTED:
        print(
            "warning: Latin Modern OTFs not found; using the next available serif fallback",
            file=sys.stderr,
        )
        _FONT_WARNING_EMITTED = True
    return resolved_paths


def apply_style() -> list[Path]:
    """Apply the shared arXiv/LaTeX figure style."""

    font_paths = _register_latin_modern()
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Latin Modern Roman",
                "CMU Serif",
                "TeX Gyre Termes",
                "Nimbus Roman",
                "DejaVu Serif",
            ],
            "mathtext.fontset": "cm",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.linewidth": 0.6,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.fontsize": 8,
            "legend.frameon": False,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "lines.linewidth": 1.2,
            "lines.markersize": 4,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
            "savefig.transparent": False,
        }
    )
    return font_paths


def load_csv(path: Path, expected_header: tuple[str, ...]) -> list[dict[str, str]]:
    """Load one source CSV while preserving its exact text fields."""

    if not path.is_file():
        raise FileNotFoundError(
            f"missing figure source CSV: {path}; regenerate it with "
            "`.venv/bin/python -m sbqos.reproduce_all`"
        )
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual_header = tuple(reader.fieldnames or ())
        if actual_header != expected_header:
            raise ValueError(
                f"unexpected CSV header in {path}: {actual_header!r}; "
                f"expected {expected_header!r}"
            )
        return list(reader)


def _floats(rows: list[dict[str, str]], key: str) -> np.ndarray:
    return np.asarray([float(row[key]) for row in rows], dtype=np.float64)


def _ints(rows: list[dict[str, str]], key: str) -> np.ndarray:
    return np.asarray([int(row[key]) for row in rows], dtype=np.int64)


def _ordered_rows_for_domain(
    figure_id: str,
    rows: list[dict[str, str]],
    key_fn: Callable[[dict[str, str]], object],
    expected_keys: tuple[object, ...],
    domain_name: str,
) -> list[dict[str, str]]:
    observed = [key_fn(row) for row in rows]
    counts = Counter(observed)
    expected = set(expected_keys)
    missing = [key for key in expected_keys if key not in counts]
    unexpected = [key for key in counts if key not in expected]
    duplicates = [key for key, count in counts.items() if count > 1]
    if missing or unexpected or duplicates:
        raise ValueError(
            f"{figure_id}: invalid {domain_name}; missing={missing!r}; "
            f"unexpected={unexpected!r}; duplicates={duplicates!r}"
        )
    by_key = {key_fn(row): row for row in rows}
    return [by_key[key] for key in expected_keys]


def _canonical_rows(figure_id: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Validate a figure's complete domain and return rows in specification order."""

    if figure_id == "F3":
        return _ordered_rows_for_domain(
            "F3", rows, lambda row: int(row["budget"]), _F3_BUDGETS, "budget domain"
        )
    if figure_id == "F4":
        return _ordered_rows_for_domain(
            "F4", rows, lambda row: int(row["rung"]), (1, 2), "rung domain"
        )
    if figure_id == "F5":
        expected = tuple(
            (point, predictor)
            for point in _F5_POINTS
            for predictor in ("static",) + _F5_PREDICTORS
        )
        return _ordered_rows_for_domain(
            "F5",
            rows,
            lambda row: (row["point"], row["predictor"]),
            expected,
            "point/predictor domain",
        )
    if figure_id == "F6":
        observed_scenarios = {row["scenario"] for row in rows}
        expected_scenarios = set(_F6_SCENARIOS)
        missing = [scenario for scenario in _F6_SCENARIOS if scenario not in observed_scenarios]
        unexpected = sorted(observed_scenarios - expected_scenarios)
        if missing or unexpected:
            raise ValueError(
                "F6: invalid scenario domain; "
                f"missing={missing!r}; unexpected={unexpected!r}; duplicates=[]"
            )
        ordered: list[dict[str, str]] = []
        for scenario in _F6_SCENARIOS:
            panel_rows = [row for row in rows if row["scenario"] == scenario]
            ordered.extend(
                _ordered_rows_for_domain(
                    "F6",
                    panel_rows,
                    lambda row: int(row["N"]),
                    _F6_N_GRID,
                    f"N grid for scenario {scenario!r}",
                )
            )
        return ordered
    if figure_id == "F7":
        return _ordered_rows_for_domain(
            "F7", rows, lambda row: row["scenario"], _F7_SCENARIOS, "scenario domain"
        )
    if figure_id == "F8":
        return _ordered_rows_for_domain(
            "F8", rows, lambda row: int(row["N"]), _F8_N_GRID, "N domain"
        )
    if figure_id == "F9":
        return _ordered_rows_for_domain(
            "F9", rows, lambda row: row["policy"], _F9_POLICIES, "policy domain"
        )
    raise ValueError(f"unsupported figure id: {figure_id}")


def fig_F3(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F3", rows)
    fig, ax = plt.subplots(figsize=(4.8, 3.1))
    budget = _ints(rows, "budget")
    random_min = _floats(rows, "random_min")
    random_max = _floats(rows, "random_max")

    band = ax.fill_between(
        budget,
        random_min,
        random_max,
        color=BLACK,
        alpha=0.12,
        linewidth=0,
        label="random (min-max over 10 seeds)",
        zorder=1,
    )
    random_line, = ax.plot(
        budget,
        _floats(rows, "random_mean"),
        color=BLACK,
        linestyle=":",
        label="random (mean of 10 seeds)",
        zorder=2,
    )
    lex_line, = ax.plot(
        budget,
        _floats(rows, "lex"),
        color=VERMILION,
        linestyle="--",
        marker="s",
        label="lexicographic",
        zorder=3,
    )
    greedy_line, = ax.plot(
        budget,
        _floats(rows, "greedy"),
        color=BLUE,
        linestyle="-",
        marker="o",
        label="greedy (chain rule)",
        zorder=5,
    )
    ax.set(xlabel="check budget $b$", ylabel=r"residual trace  $\mathrm{tr}\,\Xi$")
    ax.set_xticks(budget)
    ax.set_ylim(0.15, 0.45)
    ax.legend(
        [greedy_line, lex_line, random_line, band],
        [
            "greedy (chain rule)",
            "lexicographic",
            "random (mean of 10 seeds)",
            "random (min-max over 10 seeds)",
        ],
        loc="upper right",
        fontsize=7,
    )
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.17, top=0.97)
    return fig


def fig_F4(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F4", rows)
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    values = _floats(rows, "trace_xi")
    floor = float(rows[0]["mmse_floor"])
    x = np.arange(2)
    ax.bar(x, values, width=0.5, color=SKY_BLUE, edgecolor=BLACK, linewidth=0.6, zorder=2)
    ax.axhline(
        floor,
        color=BLACK,
        linestyle="--",
        linewidth=1.2,
        label="exact optimal-decoder MMSE\n= 47291/1715000",
        zorder=3,
    )
    for xpos, value, label in zip(x, values, ("0.083680", "0.027575"), strict=True):
        ax.annotate(
            label,
            (xpos, value),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7,
        )
    ax.set_xticks(x, ("degree-1", "degree-2-complete"))
    ax.set(xlabel="ladder rung", ylabel=r"residual trace  $\mathrm{tr}\,\Xi$")
    ax.set_ylim(0.0, 0.10)
    ax.legend(loc="upper right", fontsize=7)
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.18, top=0.96)
    return fig


_F5_PREDICTORS = (
    "oracle",
    "exact_filter",
    "run_length_K2",
    "run_length_K4",
    "run_length_K8",
    "run_length_K16",
    "rounding_K2",
    "rounding_K4",
    "rounding_K8",
    "rounding_K16",
)
_F5_LABELS = (
    "oracle",
    "exact filter",
    "run-length K=2",
    "run-length K=4",
    "run-length K=8",
    "run-length K=16",
    "rounding K=2",
    "rounding K=4",
    "rounding K=8",
    "rounding K=16",
)
_F5_POINTS = ("frozen_defaults", "loud_mode")


def fig_F5(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F5", rows)
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.0), sharey=True)
    color_by_predictor = {
        "oracle": BLACK,
        "exact_filter": BLUE,
        **{f"run_length_K{k}": GREEN for k in (2, 4, 8, 16)},
        **{f"rounding_K{k}": VERMILION for k in (2, 4, 8, 16)},
    }
    label_by_predictor = dict(zip(_F5_PREDICTORS, _F5_LABELS, strict=True))
    point_titles = (("frozen_defaults", "(a) frozen defaults"), ("loud_mode", "(b) loud mode"))

    for ax, (point, panel_title) in zip(axes, point_titles, strict=True):
        by_predictor = {row["predictor"]: float(row["gap"]) for row in rows if row["point"] == point}
        predictors = list(_F5_PREDICTORS)
        values = [by_predictor[name] for name in predictors]
        x = np.arange(len(values))
        bars = ax.bar(
            x,
            values,
            color=[color_by_predictor[name] for name in predictors],
            edgecolor=BLACK,
            linewidth=0.4,
            width=0.72,
        )
        ax.axhline(0.0, color=BLACK, linewidth=0.8)
        positions = {name: idx for idx, name in enumerate(predictors)}
        ax.axvline(
            (positions["exact_filter"] + positions["run_length_K2"]) / 2,
            color=BLACK,
            linestyle=":",
            linewidth=0.6,
        )
        ax.axvline(
            (positions["run_length_K16"] + positions["rounding_K2"]) / 2,
            color=BLACK,
            linestyle=":",
            linewidth=0.6,
        )
        ax.set_xticks(
            x,
            [label_by_predictor[name] for name in predictors],
            rotation=45,
            ha="right",
            rotation_mode="anchor",
        )
        ax.set_ylim(-0.08, 0.065)
        ax.text(0.02, 1.035, panel_title, transform=ax.transAxes, va="bottom", fontsize=8, fontweight="bold")
        ax.set_xlabel("predictor")
        if point == "frozen_defaults":
            for bar, value in zip(bars, values, strict=True):
                positive = value >= 0
                ax.annotate(
                    f"{value:+.2g}",
                    (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 2 if positive else -2),
                    textcoords="offset points",
                    ha="center",
                    va="bottom" if positive else "top",
                    fontsize=7,
                    rotation=90,
                )
        if point == "loud_mode":
            xpos = positions["rounding_K16"]
            ax.annotate(
                "+0.0301",
                (xpos, by_predictor["rounding_K16"]),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
            )

    axes[0].set_ylabel("NLL gap vs. static predictor (nats / round)")
    fig.legend(
        handles=[
            Patch(facecolor=BLACK, edgecolor=BLACK, label="oracle"),
            Patch(facecolor=BLUE, edgecolor=BLACK, label="exact filter"),
            Patch(facecolor=GREEN, edgecolor=BLACK, label="run-length"),
            Patch(facecolor=VERMILION, edgecolor=BLACK, label="rounding"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=4,
    )
    fig.subplots_adjust(left=0.105, right=0.99, bottom=0.37, top=0.77, wspace=0.08)
    return fig


_F6_SERIES = (
    ("w2a", "W2a: legacy statistic, recalibrated null", SKY_BLUE, "-", "o", 1.2),
    ("w2b", "W2b: quadratic statistic (W2c naming shares this curve)", BLUE, "-", "s", 1.6),
    ("w2d", "W2d: sequential (CUSUM)", GREEN, "--", "^", 1.2),
    ("baseline", "baseline", BLACK, "-", "x", 1.2),
    ("baseline_cusum", "baseline CUSUM", BLACK, "--", "+", 1.2),
)
_F6_SCENARIOS = ("0_3", "2_5", "4_8")
_F7_SCENARIOS = ("0_3", "2_5", "4_8")
_F9_POLICIES = ("static", "scheduled_matched", "scheduled_frequent", "witness", "oracle")
_F9_LABELS = ("static", "scheduled\n(budget-matched)", "scheduled\n(frequent)", "witness-\ntriggered", "oracle")


def _jitter_coincident(source: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Offset exactly coincident F6 markers by at most 0.012 for display."""

    displayed = {name: values.copy() for name, values in source.items()}
    names = list(source)
    for col in range(len(next(iter(source.values())))):
        groups: dict[float, list[str]] = {}
        for name in names:
            groups.setdefault(float(source[name][col]), []).append(name)
        for members in groups.values():
            if len(members) > 1:
                offsets = np.linspace(-0.012, 0.012, len(members))
                for name, offset in zip(members, offsets, strict=True):
                    displayed[name][col] += offset
    return displayed


def fig_F6(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F6", rows)
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 3.1), sharey=True)
    panels = (
        ("0_3", "(a) (0,3): original E2 scenario"),
        ("2_5", "(b) (2,5): near parity"),
        ("4_8", "(c) (4,8): off both logical supports"),
    )
    ticks = [250, 500, 1000, 2000, 4000, 8000, 16000]
    legend_handles = []

    for ax, (scenario, panel_title) in zip(axes, panels, strict=True):
        panel_rows = [row for row in rows if row["scenario"] == scenario]
        x = _ints(panel_rows, "N")
        source = {key: _floats(panel_rows, key) for key, *_ in _F6_SERIES}
        displayed = _jitter_coincident(source)
        for key, label, color, linestyle, marker, linewidth in _F6_SERIES:
            line, = ax.plot(
                x,
                displayed[key],
                color=color,
                linestyle=linestyle,
                marker=marker,
                linewidth=linewidth,
                label=label,
            )
            if scenario == "0_3":
                legend_handles.append(line)
        ax.set_xscale("log")
        ax.set_xticks(ticks, [str(value) for value in ticks])
        ax.tick_params(axis="x", labelrotation=45)
        ax.set_xlim(210, 19000)
        ax.set_ylim(-0.02, 1.02)
        ax.set_yticks([0.0, 0.5, 1.0])
        ax.text(
            0.0,
            1.03,
            panel_title,
            transform=ax.transAxes,
            va="bottom",
            fontsize=7.2,
            fontweight="bold",
        )

    axes[0].set_ylabel("detection fraction (10 seeds)")
    fig.supxlabel("shots $N$", y=0.22, fontsize=9)
    fig.legend(
        handles=legend_handles,
        labels=[entry[1] for entry in _F6_SERIES],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.005),
        ncol=3,
        fontsize=7,
        handlelength=2.3,
        columnspacing=1.0,
    )
    fig.text(
        0.675,
        0.16,
        r"markers at coincident values are offset by $\leq 0.015$ for legibility",
        ha="center",
        fontsize=7,
    )
    fig.subplots_adjust(left=0.09, right=0.995, bottom=0.37, top=0.88, wspace=0.12)
    return fig


def fig_F7(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F7", rows)
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    scenario_order = _F7_SCENARIOS
    by_scenario = {row["scenario"]: row for row in rows}
    overlap = np.asarray([float(by_scenario[s]["mean_overlap"]) for s in scenario_order])
    named = np.asarray([float(by_scenario[s]["named_in_pair_count"]) / 10.0 for s in scenario_order])
    x = np.arange(3)
    width = 0.34
    bars_overlap = ax.bar(
        x - width / 2,
        overlap,
        width,
        color=BLUE,
        edgecolor=BLACK,
        linewidth=0.5,
        label="mean logical-direction overlap",
        zorder=2,
    )
    bars_named = ax.bar(
        x + width / 2,
        named,
        width,
        color=ORANGE,
        edgecolor=BLACK,
        linewidth=0.5,
        label="seeds naming a true-pair qubit / 10",
        zorder=2,
    )
    overlap_line = ax.axhline(
        0.6,
        color=BLACK,
        linestyle="--",
        linewidth=0.8,
        label="registered overlap bar (0.6)",
        zorder=1,
    )
    naming_line = ax.axhline(
        0.8,
        color=BLACK,
        linestyle=":",
        linewidth=0.8,
        label="registered naming bar (8/10)",
        zorder=1,
    )
    ax.annotate(
        "0.869",
        (bars_overlap[2].get_x() + bars_overlap[2].get_width() / 2, overlap[2]),
        xytext=(0, 3),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7,
    )
    ax.annotate(
        "3/10",
        (bars_named[2].get_x() + bars_named[2].get_width() / 2, named[2]),
        xytext=(0, 3),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7,
    )
    ax.set_xticks(x, ("(0,3)", "(2,5)", "(4,8)"))
    ax.set(xlabel="injection pair", ylabel="fraction")
    ax.set_ylim(0.0, 1.0)
    ax.legend(
        [bars_overlap, bars_named, overlap_line, naming_line],
        [
            "mean logical-direction overlap",
            "seeds naming a true-pair qubit / 10",
            "registered overlap bar (0.6)",
            "registered naming bar (8/10)",
        ],
        loc="upper left",
        fontsize=7,
        ncol=1,
        frameon=True,
        framealpha=1.0,
        edgecolor="none",
        facecolor="white",
    )
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.18, top=0.97)
    return fig


def fig_F8(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F8", rows)
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    x = _ints(rows, "N")
    ax.plot(
        x,
        _floats(rows, "witness_frac"),
        color=BLUE,
        linestyle="-",
        marker="s",
        label="corrected witness (W2b)",
        zorder=3,
    )
    ax.plot(
        x,
        _floats(rows, "baseline_frac"),
        color=BLACK,
        linestyle="-",
        marker="x",
        label="pymatching baseline",
        zorder=2,
    )
    ax.axvline(50, color=BLUE, linestyle=":", linewidth=0.8)
    ax.axvline(100, color=BLACK, linestyle=":", linewidth=0.8)
    ax.text(0.48, 0.64, "witness reaches 1.0 at $N = 50$", transform=ax.transAxes, color=BLUE, fontsize=7, ha="left")
    ax.text(0.48, 0.58, "baseline reaches 1.0 at $N = 100$", transform=ax.transAxes, color=BLACK, fontsize=7, ha="left")
    ax.text(0.48, 0.52, "ratio 2x = registered bar, exactly", transform=ax.transAxes, color=BLACK, fontsize=7, ha="left")
    ax.set_xscale("log")
    ax.set_xticks(x, [str(value) for value in x])
    ax.tick_params(axis="x", labelrotation=45)
    ax.set_ylim(-0.02, 1.02)
    ax.set(xlabel=r"detector-stream shots $N$", ylabel="detection fraction (10 seeds)")
    ax.legend(loc="lower right", fontsize=7)
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.2, top=0.97)
    return fig


def fig_F9(rows: list[dict[str, str]]) -> Figure:
    rows = _canonical_rows("F9", rows)
    fig, ax = plt.subplots(figsize=(4.8, 3.3))
    policy_order = _F9_POLICIES
    labels = _F9_LABELS
    by_policy = {row["policy"]: row for row in rows}
    policies = list(policy_order)
    label_by_policy = dict(zip(policy_order, labels, strict=True))
    color_by_policy = {
        "static": GREY,
        "scheduled_matched": BLACK,
        "scheduled_frequent": BLACK,
        "witness": BLUE,
        "oracle": GREY,
    }
    errors = np.asarray([float(by_policy[p]["mean_post_drift_error"]) for p in policies])
    events = np.asarray([float(by_policy[p]["mean_recalibration_events"]) for p in policies])
    x = np.arange(len(policies))
    bars = ax.bar(
        x,
        errors,
        color=[color_by_policy[policy] for policy in policies],
        edgecolor=BLACK,
        linewidth=0.6,
        width=0.68,
        zorder=2,
    )
    oracle = float(by_policy["oracle"]["mean_post_drift_error"])
    ax.axhline(oracle, color="#777777", linestyle="--", linewidth=0.8, zorder=1)
    ax.text(
        0.54,
        oracle - 0.0010,
        "oracle ceiling",
        transform=ax.get_yaxis_transform(),
        ha="left",
        va="top",
        fontsize=7,
        color="#555555",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 0.5},
    )

    for bar, policy, event_count in zip(bars, policies, events, strict=True):
        weight = "bold" if policy in {"scheduled_matched", "witness"} else "normal"
        ax.annotate(
            f"{event_count:.1f} events",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7,
            fontweight=weight,
            clip_on=False,
        )

    ax.set_xticks(x, [label_by_policy[policy] for policy in policies])
    ax.tick_params(axis="x", labelsize=7, pad=2)
    ax.set_ylim(0.08, 0.125)
    ax.set_ylabel("mean post-drift logical error (10 seeds)")
    ax.text(
        0.98,
        0.98,
        "axis starts at 0.08\nbar labels: mean recalibration events per seed",
        transform=ax.transAxes,
        fontsize=7,
        ha="right",
        va="top",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1.0},
    )
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.2, top=0.96)
    return fig


FIGURE_BUILDERS: dict[str, Callable[[list[dict[str, str]]], Figure]] = {
    "F3": fig_F3,
    "F4": fig_F4,
    "F5": fig_F5,
    "F6": fig_F6,
    "F7": fig_F7,
    "F8": fig_F8,
    "F9": fig_F9,
}


def _pairs(rows: list[dict[str, str]], x_key: str, y_key: str) -> list[tuple[object, float]]:
    pairs: list[tuple[object, float]] = []
    for row in rows:
        x: object = int(row[x_key]) if row[x_key].isdigit() else row[x_key]
        pairs.append((x, float(row[y_key])))
    return pairs


def _plotted_arrays(figure_id: str, rows: list[dict[str, str]]) -> dict[str, list[tuple[object, float]]]:
    rows = _canonical_rows(figure_id, rows)
    if figure_id == "F3":
        return {key: _pairs(rows, "budget", key) for key in ("greedy", "lex", "random_mean", "random_min", "random_max")}
    if figure_id == "F4":
        return {key: _pairs(rows, "rung", key) for key in ("trace_xi", "mmse_floor")}
    if figure_id == "F5":
        arrays = {}
        for point in _F5_POINTS:
            point_rows = [row for row in rows if row["point"] == point]
            by_predictor = {row["predictor"]: row for row in point_rows}
            ordered = [by_predictor[name] for name in ("static",) + _F5_PREDICTORS]
            arrays[point] = [(row["predictor"], float(row["gap"])) for row in ordered]
        return arrays
    if figure_id == "F6":
        arrays = {}
        for scenario in _F6_SCENARIOS:
            panel = [row for row in rows if row["scenario"] == scenario]
            for key, *_ in _F6_SERIES:
                arrays[f"{scenario}.{key} (source, before display jitter)"] = _pairs(panel, "N", key)
        return arrays
    if figure_id == "F7":
        return {
            "mean logical-direction overlap": [(row["scenario"], float(row["mean_overlap"])) for row in rows],
            "seeds naming a true-pair qubit / 10": [
                (row["scenario"], float(row["named_in_pair_count"]) / 10.0) for row in rows
            ],
            "modal qubit (annotation data)": [(row["scenario"], float(row["modal_qubit"])) for row in rows],
        }
    if figure_id == "F8":
        return {key: _pairs(rows, "N", key) for key in ("witness_frac", "baseline_frac")}
    if figure_id == "F9":
        by_policy = {row["policy"]: row for row in rows}
        return {
            "mean post-drift logical error": [
                (policy, float(by_policy[policy]["mean_post_drift_error"])) for policy in _F9_POLICIES
            ],
            "mean recalibration events (annotation data)": [
                (policy, float(by_policy[policy]["mean_recalibration_events"])) for policy in _F9_POLICIES
            ],
        }
    raise ValueError(f"unsupported figure id: {figure_id}")


def _save_figure(fig: Figure, pdf_path: Path, png_path: Path | None) -> None:
    fig.savefig(pdf_path, format="pdf", metadata=PDF_METADATA)
    if png_path is not None:
        fig.savefig(
            png_path,
            format="png",
            dpi=300,
            metadata=PNG_METADATA,
            pil_kwargs={"compress_level": 9, "optimize": False},
        )


def _parse_only(value: str | None, parser: argparse.ArgumentParser) -> list[str]:
    if value is None:
        return list(FIGURE_FILES)
    selected = [item.strip().upper() for item in value.split(",") if item.strip()]
    unknown = [item for item in selected if item not in FIGURE_FILES]
    if unknown:
        parser.error(f"unknown figure id(s) in --only: {', '.join(unknown)}")
    if not selected:
        parser.error("--only must name at least one of F3,F4,F5,F6,F7,F8,F9")
    return list(dict.fromkeys(selected))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("paper/figures/generated"))
    parser.add_argument("--only", help="comma-separated subset, for example F3,F5")
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    png_group = parser.add_mutually_exclusive_group()
    png_group.add_argument("--png", dest="png", action="store_true", help="write PNG previews (default)")
    png_group.add_argument("--no-png", dest="png", action="store_false", help="write PDF files only")
    parser.set_defaults(png=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    selected = _parse_only(args.only, parser)
    font_paths = apply_style()
    args.out.mkdir(parents=True, exist_ok=True)

    print("environment:")
    print(f"  matplotlib {matplotlib.__version__}")
    try:
        pillow_version = version("Pillow")
    except PackageNotFoundError:
        pillow_version = "unknown"
    print(f"  pillow {pillow_version}")
    print(f"  MPLCONFIGDIR={Path(os.environ['MPLCONFIGDIR']).expanduser().resolve()}")
    fonts = ", ".join(str(path) for path in font_paths) if font_paths else "fallback (Latin Modern not found)"
    print(f"  fonts: {fonts}")

    for figure_id in selected:
        relative_source, expected_header = SOURCE_SPECS[figure_id]
        rows = load_csv(args.artifacts / relative_source, expected_header)
        fig = FIGURE_BUILDERS[figure_id](rows)
        stem = FIGURE_FILES[figure_id]
        pdf_path = args.out / f"{stem}.pdf"
        png_path = args.out / f"{stem}.png" if args.png else None
        _save_figure(fig, pdf_path, png_path)
        plt.close(fig)

        print(figure_id)
        print(f"  PDF: {pdf_path}")
        print(f"  PNG: {png_path if png_path is not None else 'disabled'}")
        for series, values in _plotted_arrays(figure_id, rows).items():
            print(f"  {series}: {values!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
