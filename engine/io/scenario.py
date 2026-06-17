"""Build the initial Scenario for a run, from real or synthetic data.

This is the single place that knows real data from synthetic. Everything
downstream — the runner and the Simulator — receives a `Scenario` and is blind
to where it came from.
"""

from typing import NamedTuple

from engine.config import ScenarioConfig
from engine.core.agents import Constructor, House, Household, Region
import numpy as np


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
    return _generate_synthetic(scenario)


def _read_real(scenario: ScenarioConfig) -> Scenario:
    # TODO: load the agent data files under data/<scenario.path>.
    return Scenario([], [], [], [])


def _generate_synthetic(scenario: ScenarioConfig) -> Scenario:
    """
    Generates a full synthetic scenario from a parsed YAML configuration dictionary.
    """
    # 1. Initialize the shared deterministic random generator
    rng = np.random.default_rng(scenario["seed"])
    
    # 2. Generate Independent Entities
    constructors = generate_constructors(scenario["constructors"], rng)
    regions = generate_regions(scenario["geography"], rng)
    
    # 3. Generate Dependent Entities
    houses = generate_houses(scenario["houses"], regions, constructors, rng)
    households = generate_households(scenario["households"], regions, rng)

    #quando crio households façp logo assign das casas
    #generate em json e depois construtores no I/O. import so json que está no input syntetic
    #gera jsons no data. 
    
    return Scenario(
        regions=regions, 
        households=households, 
        houses=houses, 
        constructors=constructors
    )
