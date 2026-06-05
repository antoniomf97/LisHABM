from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.config import EngineConfig, SimConfig


def test_engine_config_requires_scenario():
    with pytest.raises(ValidationError):
        EngineConfig()  # type: ignore[call-arg]


def test_engine_config_defaults(make_scenario_config):
    config = EngineConfig(scenario=make_scenario_config())
    assert config.sim.n_ticks == 1000
    assert config.sim.seed == 42
    assert config.demographics.enabled is True
    assert config.construction.enabled is True
    assert config.market.enabled is True
    assert config.output.format == "csv"
    assert config.output.every_n_ticks == 10


def test_scenario_config_path_is_path_object(make_scenario_config):
    scenario = make_scenario_config(path="data/test")
    assert isinstance(scenario.path, Path)


def test_scenario_config_invalid_source_raises(make_scenario_config):
    with pytest.raises(ValidationError):
        make_scenario_config(source="unknown")


def test_sim_config_custom_values():
    sim = SimConfig(n_ticks=500, seed=99)
    assert sim.n_ticks == 500
    assert sim.seed == 99


def test_output_config_every_n_ticks_must_be_positive(make_scenario_config):
    with pytest.raises(ValidationError):
        EngineConfig(
            scenario=make_scenario_config(),
            output={"every_n_ticks": 0},  # type: ignore[arg-type]
        )
