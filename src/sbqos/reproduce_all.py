"""Run registered experiment configs and verify their manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from sbqos.artifacts import load_config, verify_manifest
from sbqos.experiments import (
    e1_coverage,
    e2_drift_witness,
    e3_check_selection,
    e4_existence,
    e5_decoder_memory,
    e6_slack,
    e7_witness_ladder,
    e8_circuit_level,
    e9_control_loop,
)
from sbqos.experiments.common import run_dir_for


Runner = Callable[[str], None]


RUNNERS: dict[str, Runner] = {
    "e1": e1_coverage.main,
    "e2": e2_drift_witness.main,
    "e3": e3_check_selection.main,
    "e4": e4_existence.main,
    "e5": e5_decoder_memory.main,
    "e6": e6_slack.main,
    "e7": e7_witness_ladder.main,
    "e8": e8_circuit_level.main,
    "e9": e9_control_loop.main,
}


def main() -> int:
    ok = True
    config_dir = Path(__file__).resolve().parent / "configs"
    for config_path in sorted(config_dir.glob("*.json")):
        config = load_config(str(config_path))
        experiment = config["experiment"]
        runner = RUNNERS.get(experiment)
        if runner is None:
            print(f"{config_path.name}: skipped (no runner yet)")
            continue
        print(f"{config_path.name}: running")
        runner(str(config_path))
        run_dir = run_dir_for(config)
        if verify_manifest(run_dir):
            print(f"{config_path.name}: manifest ok")
        else:
            print(f"{config_path.name}: manifest mismatch")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
