"""Entry point: config file in, finished Simulators out.

Loads and validates a YAML config, builds the scenario from it (real or
synthetic — see engine/io/scenario.py), and runs the simulation ``n_runs``
times via the scheduler (one run per seed, in parallel). Returns the finished
Simulators for downstream aggregation.
"""

import argparse
from pathlib import Path

from engine.core.simulator import Simulator
from orchestration.config import load_config
from orchestration.scheduler import run_all

# CLI config names resolve to configs/<name>.yaml (relative to the cwd).
CONFIG_DIR = Path("configs")


def run(config_path: str | Path) -> list[Simulator]:
    """Run all configured runs described by the config at ``config_path``."""
    config = load_config(config_path)
    return run_all(
        config.engine,
        n_runs=config.runs.n_runs,
        n_workers=config.runs.n_workers,
    )


def _resolve_config(arg: str) -> Path:
    """Resolve a CLI argument to a config file path."""
    base = Path(arg) if ("/" in arg or "\\" in arg) else CONFIG_DIR / arg
    return base.with_suffix(".yaml")


def main(argv: list[str] | None = None) -> int:
    """CLI: run the simulation for a config name or path."""
    parser = argparse.ArgumentParser(
        prog="lishabm", description="Run LisHABM simulation."
    )
    parser.add_argument(
        "config",
        help="config name in configs/, or a path to a .yaml file",
    )
    args = parser.parse_args(argv)
    path = _resolve_config(args.config)
    if not path.is_file():
        parser.error(f"config not found: {path}")

    run(path)
    return 0
