"""Engine configuration schema.

Pydantic models for everything the Simulator and I/O layer need.
Orchestration concerns (run metadata, config loading) live in
orchestration/config.py.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


# ── Simulation parameters ────────────────────────────────────
class SimConfig(BaseModel):
    n_ticks: int = 1000
    seed: int = 42


# ── Scenario: where the initial world comes from ─────────────
class ScenarioConfig(BaseModel):
    source: Literal["real", "synthetic"]
    path: Path  # directory under data/ holding the data files or recipe


# ── Module parameters ────────────────────────────────────────
class DemographicsConfig(BaseModel):
    enabled: bool = True


class ConstructionConfig(BaseModel):
    enabled: bool = True


class MarketConfig(BaseModel):
    enabled: bool = True


# ── Output ───────────────────────────────────────────────────
class OutputConfig(BaseModel):
    dir: Path = Path("data/outputs")
    format: Literal["csv", "pickle"] = "csv"
    every_n_ticks: int = Field(default=10, gt=0)
    record: list[str] = Field(
        default_factory=lambda: ["households", "houses", "market"]
    )


# ── Engine config ─────────────────────────────────────────────
# Everything the Simulator and I/O layer receive. No orchestration
# concerns (run name, how it was launched) live here.
class EngineConfig(BaseModel):
    sim: SimConfig = SimConfig()
    scenario: ScenarioConfig
    demographics: DemographicsConfig = DemographicsConfig()
    construction: ConstructionConfig = ConstructionConfig()
    market: MarketConfig = MarketConfig()
    output: OutputConfig = OutputConfig()
