"""Engine configuration schema.

Pydantic models for everything the Simulator and I/O layer need.
Orchestration concerns (run metadata, config loading) live in
orchestration/config.py.
"""

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Simulation parameters ────────────────────────────────────
class SimConfig(BaseModel):
    n_ticks: int = 1000
    seed: int = 42
    months_per_tick: int = Field(default=3, gt=0)  # length of one tick in months


# ── Scenario: where the initial world comes from ─────────────
class ScenarioConfig(BaseModel):
    source: Literal["real", "synthetic"]
    path: Path  # directory under data/ holding the data files or recipe
    cache: Path | None = None  # synthetic only: pickle loaded if present, else written


# ── Module parameters ────────────────────────────────────────
class AgeBandRate(BaseModel):
    """An annual probability for ages ``min_age`` to ``max_age`` (inclusive)."""

    model_config = ConfigDict(extra="forbid")
    min_age: int = Field(ge=0)
    max_age: int = Field(ge=0)  # inclusive
    rate: float = Field(ge=0.0, le=1.0)  # annual probability

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        if self.min_age > self.max_age:
            raise ValueError(f"min_age {self.min_age} > max_age {self.max_age}")
        return self


def _check_no_overlap(bands: list[AgeBandRate], name: str) -> None:
    ordered = sorted(bands, key=lambda b: b.min_age)
    for prev, band in zip(ordered, ordered[1:]):
        if band.min_age <= prev.max_age:
            raise ValueError(
                f"{name}: band {band.min_age}-{band.max_age} overlaps "
                f"{prev.min_age}-{prev.max_age}"
            )


class ArtificialDemographicsConfig(BaseModel):
    """Stylised demographics: rules and rates are assumptions, not calibrated.

    Each variant of a module has its own schema, tagged by ``model``. An empty
    band list switches that event off, so the defaults change nothing.
    """

    model_config = ConfigDict(extra="forbid")
    model: Literal["artificial"] = "artificial"
    enabled: bool = True
    adult_age: int = Field(default=18, ge=0)
    mortality: dict[Literal["F", "M"], list[AgeBandRate]] = Field(default_factory=dict)
    fertility: list[AgeBandRate] = Field(default_factory=list)
    female_birth_share: float = Field(default=0.5, ge=0.0, le=1.0)
    separation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    partnership: list[AgeBandRate] = Field(default_factory=list)
    max_partner_age_gap: int = Field(default=10, ge=0)
    leave_home: list[AgeBandRate] = Field(default_factory=list)
    min_income_to_leave: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def _check_bands(self) -> Self:
        for sex, bands in self.mortality.items():
            _check_no_overlap(bands, f"mortality.{sex}")
        _check_no_overlap(self.fertility, "fertility")
        _check_no_overlap(self.partnership, "partnership")
        _check_no_overlap(self.leave_home, "leave_home")
        return self


# One variant today. A second variant turns this into
# Annotated[ArtificialDemographicsConfig | OtherConfig, Field(discriminator="model")].
DemographicsConfig = ArtificialDemographicsConfig


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
