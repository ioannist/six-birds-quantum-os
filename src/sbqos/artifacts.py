"""config loading, result writing, manifest hashing"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from importlib import metadata
from pathlib import Path
from types import TracebackType
from typing import Any


Schema = dict[str, Any]


CONFIG_SCHEMAS: dict[str, Schema] = {
    "e1": {
        "experiment": str,
        "seed": int,
        "rep3_p": str,
        "rep5_p": str,
        "surf3_p": str,
    },
    "e2": {
        "experiment": str,
        "seed": int,
        "surf3_p": str,
        "inject_q": str,
        "inject_pair": [int],
        "n_grid": [int],
        "n_seeds": int,
        "bootstrap_B": int,
        "null_runs": int,
        "baseline_model_shots": int,
        "n5_r": str,
        "n5_leak_qubit": int,
        "n5_window_shots": int,
        "n5_windows": int,
        "detect_seeds_required": int,
    },
    "e3": {
        "experiment": str,
        "seed": int,
        "surf3_p": str,
        "rep3_p": str,
        "surf5_p": str,
        "n_random_baselines": int,
        "tol_stop": float,
    },
    "e4": {
        "experiment": str,
        "seed": int,
        "taus": [int],
        "delta_max": float,
        "cd_max": float,
        "eps_stable": str,
        "models": [str],
        "p_sweep": [str],
        "n5_horizons": [int],
        "n5_declared_horizon": int,
        "stream_length": int,
    },
    "e5": {
        "experiment": str,
        "seed": int,
        "n4_p0": str,
        "n4_s": str,
        "n5_p": str,
        "n5_r": str,
        "trap_p0": str,
        "trap_p1": str,
        "alpha": str,
        "payoff_rounds": int,
        "payoff_v2_rounds": int,
        "payoff_v2_run_length_Ks": [int],
        "payoff_v2_rounding_Ks": [int],
        "payoff_v2_points": [{"p0": str, "s": str, "label": str}],
        "belief_bfs_depth": int,
        "belief_bfs_cap": int,
    },
    "e6": {
        "experiment": str,
        "seed": int,
        "rep5_p": str,
        "surf3_p": str,
        "lambda_tol": float,
        "n_proxy_seeds": int,
        "consequence_shots": int,
    },
    "e7": {
        "experiment": str,
        "seed": int,
        "surf3_p": str,
        "inject_q": str,
        "inject_pairs": [[int]],
        "n_grid": [int],
        "n_seeds": int,
        "bootstrap_B": int,
        "null_runs": int,
        "detect_seeds_required": int,
        "baseline_model_shots": int,
        "naming_step": str,
        "cusum_run_length": int,
        "cusum_B": int,
        "cusum_target_false_alarm": float,
    },
    "e8": {
        "experiment": str,
        "seed": int,
        "distance": int,
        "rounds": int,
        "p0": str,
        "p1_multiplier": int,
        "n_grid": [int],
        "n_seeds": int,
        "detect_seeds_required": int,
        "bootstrap_B": int,
        "null_runs": int,
        "N_cal": int,
        "baseline_calibration_shots": int,
    },
    "e9": {
        "experiment": str,
        "seed": int,
        "distance": int,
        "rounds": int,
        "p0": str,
        "measure_multiplier": int,
        "E_total": int,
        "drift_epoch": int,
        "shots_per_epoch": int,
        "n_seeds": int,
        "N_cal": int,
        "bootstrap_B": int,
        "candidate_multipliers": [int],
        "N_curve": int,
        "schedule_K_matched": int,
        "schedule_K_frequent": int,
    }
}


def load_config(path: str) -> dict:
    """Load and validate a JSON experiment config."""
    with Path(path).open("r", encoding="utf-8") as f:
        config = json.load(f)
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")
    experiment = config.get("experiment")
    if not isinstance(experiment, str):
        raise ValueError("config key 'experiment' must be str")
    if experiment not in CONFIG_SCHEMAS:
        raise ValueError(f"unknown experiment schema: {experiment!r}")
    _validate_schema(config, CONFIG_SCHEMAS[experiment], path="")
    return config


def parse_fraction(s: str) -> Fraction:
    """Parse a config probability string such as '1/20' exactly."""
    if not isinstance(s, str):
        raise TypeError("fraction config values must be strings")
    return Fraction(s)


@dataclass
class Run:
    config: dict
    out_dir: str | Path

    def __post_init__(self) -> None:
        self.path = Path(self.out_dir)

    def __enter__(self) -> "Run":
        self.path.mkdir(parents=True, exist_ok=True)
        _write_json(self.path / "config.json", self.config)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            return
        _write_json(self.path / "environment.json", _environment())
        _write_json(self.path / "manifest.json", _manifest(self.path))

    def write_result(self, results: dict) -> None:
        # Python 3.10's JSON encoder emits shortest round-trip float spellings,
        # which is the repr-consistent behavior required for persisted results.
        _write_json(self.path / "results.json", results)

    def save_figure(self, fig: Any, name: str, csv_rows: list[list], csv_header: list[str]) -> None:
        fig.savefig(self.path / f"{name}.png", dpi=150)
        with (self.path / f"{name}.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(csv_header)
            writer.writerows(csv_rows)


def verify_manifest(out_dir: str | Path) -> bool:
    path = Path(out_dir)
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return False
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            recorded = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(recorded, dict):
        return False
    current = _manifest(path)
    if set(recorded) != set(current):
        return False
    return all(recorded[name] == digest for name, digest in current.items())


def _validate_schema(config: dict, schema: Schema, path: str) -> None:
    for key in config:
        if key not in schema:
            dotted = f"{path}.{key}" if path else key
            raise ValueError(f"unknown config key: {dotted}")
    for key, expected in schema.items():
        dotted = f"{path}.{key}" if path else key
        if key not in config:
            raise ValueError(f"missing config key: {dotted}")
        value = config[key]
        if isinstance(expected, dict):
            if not isinstance(value, dict):
                raise ValueError(f"config key {dotted!r} must be object")
            _validate_schema(value, expected, dotted)
        elif isinstance(expected, list):
            if len(expected) != 1:
                raise ValueError(f"schema list for {dotted!r} must have one element type")
            if not isinstance(value, list):
                raise ValueError(f"config key {dotted!r} must be list")
            item_type = expected[0]
            for i, item in enumerate(value):
                if isinstance(item_type, dict):
                    if not isinstance(item, dict):
                        raise ValueError(f"config key {dotted}[{i}] must be object")
                    _validate_schema(item, item_type, f"{dotted}[{i}]")
                elif isinstance(item_type, list):
                    _validate_list(item, item_type, f"{dotted}[{i}]")
                elif not isinstance(item, item_type):
                    raise ValueError(f"config key {dotted}[{i}] must be {item_type.__name__}")
        elif not isinstance(value, expected):
            raise ValueError(f"config key {dotted!r} must be {expected.__name__}")


def _validate_list(value: Any, expected: list, dotted: str) -> None:
    if len(expected) != 1:
        raise ValueError(f"schema list for {dotted!r} must have one element type")
    if not isinstance(value, list):
        raise ValueError(f"config key {dotted!r} must be list")
    item_type = expected[0]
    for i, item in enumerate(value):
        if isinstance(item_type, dict):
            if not isinstance(item, dict):
                raise ValueError(f"config key {dotted}[{i}] must be object")
            _validate_schema(item, item_type, f"{dotted}[{i}]")
        elif isinstance(item_type, list):
            _validate_list(item, item_type, f"{dotted}[{i}]")
        elif not isinstance(item, item_type):
            raise ValueError(f"config key {dotted}[{i}] must be {item_type.__name__}")


def _write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=2)
        f.write("\n")


def _environment() -> dict:
    packages = {}
    for name in ("numpy", "scipy", "stim", "pymatching", "matplotlib"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = "unknown"
    return {
        "python": platform.python_version(),
        "packages": packages,
        "git_sha": _git_sha(),
    }


def _git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _manifest(path: Path) -> dict[str, str]:
    entries = {}
    for file_path in _covered_files(path):
        rel = file_path.relative_to(path).as_posix()
        entries[rel] = _sha256(file_path)
    return dict(sorted(entries.items()))


def _covered_files(path: Path) -> list[Path]:
    excluded = {"manifest.json", "environment.json"}
    return sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file() and file_path.relative_to(path).as_posix() not in excluded
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
