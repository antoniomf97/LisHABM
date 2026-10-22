"""Shared fixtures for the test suite.

The ``make_*`` fixtures are factories: each returns a builder function so a
test takes the defaults and overrides only the fields it cares about.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from engine.config import EngineConfig, ScenarioConfig, SimConfig

# A minimal but complete synthetic-generation recipe: 2 regions, 1
# constructor, 2 houses, 2 households. Every key the generator reads must
# be present.
MINIMAL_SYNTHETIC_RECIPE = {
    "seed": 1,
    "market_initialization": {
        "target_homeownership_rate": 0.5,
        "investor_percentage": 0.0,
        "max_investment_properties": 0,
        "max_rent_to_income_ratio": 0.35,
        "annual_rental_yield": 0.05,
    },
    "geography": {
        "regions": {
            "A": ["B"],
            "B": ["A"],
        },
    },
    "houses": {
        "total_count": 2,
        "regional_distribution": {"default_weight": 1.0},
        "typology_weights": {"T1": 1.0},
        "regional_sqm_price": {
            "default_price": {"type": "constant", "value": 1000.0},
        },
        "age_distribution": {"type": "constant", "value": 10},
        "quality_distribution": {"type": "constant", "value": 3},
    },
    "constructors": {
        "count": 1,
        "capital_distribution": {"type": "constant", "value": 100000.0},
        "size_distribution": {"type": "constant", "value": 1},
    },
    "households": {
        "total_count": 2,
        "archetypes": [
            {
                "weight": 1.0,
                "adults": 1,
                "adult_age_range": [30, 31],
                "education_weights": {1: 1.0},
                "base_income": {"type": "constant", "value": 2000.0},
                "children": {"type": "constant", "value": 0},
            },
        ],
    },
}


@pytest.fixture
def minimal_yaml() -> str:
    """A minimal but valid run-config YAML document."""
    return """\
runs:
  name: test
engine:
  sim:
    n_ticks: 1
  scenario:
    source: synthetic
    path: data/test
"""


@pytest.fixture
def make_scenario_config() -> Callable[..., ScenarioConfig]:
    """Build a ScenarioConfig; override any field via keyword.

    Defaults to ``source="real"``: ``_read_real`` is still a stub (always an
    empty Scenario), so tests that just need *a* working Simulator don't have
    to supply a real generation recipe. Tests that care about synthetic
    generation override ``source`` and ``path`` explicitly (see
    ``synthetic_recipe_path`` below).
    """

    def _make(**overrides: Any) -> ScenarioConfig:
        params: dict[str, Any] = {"source": "real", "path": Path("data/test")}
        params.update(overrides)
        return ScenarioConfig(**params)

    return _make


@pytest.fixture
def synthetic_recipe_path(tmp_path: Path) -> Path:
    """Write ``MINIMAL_SYNTHETIC_RECIPE`` to a YAML file; return its path."""
    recipe_path = tmp_path / "recipe.yaml"
    recipe_path.write_text(yaml.safe_dump(MINIMAL_SYNTHETIC_RECIPE), encoding="utf-8")
    return recipe_path


@pytest.fixture
def make_engine_config(
    make_scenario_config: Callable[..., ScenarioConfig],
) -> Callable[..., EngineConfig]:
    """Build an EngineConfig; override sim params or any sub-config via keyword."""

    def _make(n_ticks: int = 1, seed: int = 0, **overrides: Any) -> EngineConfig:
        params: dict[str, Any] = {
            "scenario": make_scenario_config(),
            "sim": SimConfig(n_ticks=n_ticks, seed=seed),
        }
        params.update(overrides)
        return EngineConfig(**params)

    return _make
