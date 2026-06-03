"""Single-run entry point: config file in, finished Simulator out.

Loads and validates a YAML config, builds the scenario from it (real or
synthetic — see engine/io/scenario.py), runs the simulation, and returns the
finished Simulator.
"""

import argparse
from pathlib import Path

from engine.core.simulator import Simulator
from orchestration.config import load_config

# CLI config names resolve to configs/<name>.yaml (relative to the cwd).
CONFIG_DIR = Path("configs")


def run(config_path: str | Path) -> Simulator:
    """Run one simulation described by the config at ``config_path``."""
    config = load_config(config_path)
    sim = Simulator(config.engine)
    sim.run()
    return sim


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
