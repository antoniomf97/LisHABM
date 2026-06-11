"""Orchestration config schema and YAML loader.

RunConfig is the top-level envelope the runner works with. It wraps
EngineConfig (which the Simulator owns) with just enough orchestration
metadata for the runner to tag and manage a run.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from engine.config import EngineConfig


class RunsConfig(BaseModel):
    """Run identity, plus how many times to repeat across how many cores.

    ``name`` labels the run and is used to name the output directory. All runs
    share the engine settings below; only the RNG seed varies per run (seed,
    seed+1, …), so results can be averaged across them.

    ``n_workers`` is left as ``None`` in config so the scheduler can pick a
    sensible default for the machine it runs on (``cpu_count() - 1``); the
    config file should not bake in a host-specific core count.
    """

    name: str
    n_runs: int = Field(default=1, gt=0)
    n_workers: int | None = Field(default=None, gt=0)


class RunConfig(BaseModel):
    runs: RunsConfig
    engine: EngineConfig


def load_config(path: str | Path) -> RunConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if raw is None:
        raise ValueError(f"config file is empty: {path}")
    return RunConfig.model_validate(raw)
