"""Shared runners, plotting helpers."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from sbqos.artifacts import Run, load_config


def setup_matplotlib() -> None:
    cache_dir = Path(tempfile.gettempdir()) / "sbqos-matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    import matplotlib

    matplotlib.use("Agg")


def run_dir_for(config: dict, base: str = "artifacts") -> Path:
    config_blob = json.dumps(config, sort_keys=True, separators=(",", ":"))
    config_hash8 = hashlib.sha256(config_blob.encode("utf-8")).hexdigest()[:8]
    experiment = str(config["experiment"])
    name = str(config.get("name", "default"))
    return Path(base) / f"{experiment}_{name}" / config_hash8


def main_template(config_path: str, runner: Callable[[dict, Run], None]) -> None:
    config = load_config(config_path)
    with Run(config, run_dir_for(config)) as run:
        runner(config, run)
