"""Shared fixtures for the test suite.

The ``make_*`` fixtures are factories: each returns a builder function so a
test takes the defaults and overrides only the fields it cares about.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from engine.config import EngineConfig, ScenarioConfig, SimConfig


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
    """Build a ScenarioConfig; override any field via keyword."""

    def _make(**overrides: Any) -> ScenarioConfig:
        params: dict[str, Any] = {"source": "synthetic", "path": Path("data/test")}
        params.update(overrides)
        return ScenarioConfig(**params)

    return _make


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
