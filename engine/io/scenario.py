"""Build the initial Scenario for a run, from real or synthetic data.

This is the single place that knows real data from synthetic. Everything
downstream — the runner and the Simulator — receives a `Scenario` and is blind
to where it came from.
"""

from typing import NamedTuple

import yaml

from engine.config import ScenarioConfig
from engine.core.agents import Constructor, House, Household, Region


class Scenario(NamedTuple):
    """A populated scenario — exactly the agent lists the Simulator takes."""

    regions: list[Region]
    households: list[Household]
    houses: list[House]
    constructors: list[Constructor]


def load_scenario(scenario: ScenarioConfig) -> Scenario:
    """Load the initial scenario described by ``scenario`` (from data/)."""
    if scenario.source == "real":
        return _read_real(scenario)
    return _read_synthetic(scenario)


def _read_real(scenario: ScenarioConfig) -> Scenario:
    # TODO: load the agent data files under data/<scenario.path>.
    return Scenario([], [], [], [])


def _read_synthetic(scenario: ScenarioConfig) -> Scenario:
    """Generate the scenario from the recipe YAML at ``scenario.path``.

    The generator (``data/input/synthetic/generator.py``) itself imports
    ``Scenario`` from this module, so this import is deferred to call time:
    importing it at module load time would be a circular import (this module
    isn't fully defined yet the first time it's loaded).
    """
    from data.input.synthetic.generator import _generate_synthetic

    config = yaml.safe_load(scenario.path.read_text(encoding="utf-8"))
    return _generate_synthetic(config)
