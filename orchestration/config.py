"""Orchestration config schema and YAML loader.

RunConfig is the top-level envelope the runner works with. It wraps
EngineConfig (which the Simulator owns) with just enough orchestration
metadata for the runner to tag and manage a run.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from engine.config import EngineConfig


class RunMetadata(BaseModel):
    name: str
    description: str = ""


class RunConfig(BaseModel):
    run: RunMetadata
    engine: EngineConfig


def load_config(path: str | Path) -> RunConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if raw is None:
        raise ValueError(f"config file is empty: {path}")
    return RunConfig.model_validate(raw)
