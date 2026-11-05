from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.config import (
    AgeBandRate,
    ArtificialDemographicsConfig,
    EngineConfig,
    SimConfig,
)


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


def test_scenario_config_cache_defaults_to_none(make_scenario_config):
    assert make_scenario_config().cache is None


def test_scenario_config_cache_is_path_object(make_scenario_config):
    scenario = make_scenario_config(cache="data/test.pkl")
    assert isinstance(scenario.cache, Path)


def test_scenario_config_invalid_source_raises(make_scenario_config):
    with pytest.raises(ValidationError):
        make_scenario_config(source="unknown")


def test_sim_config_months_per_tick_defaults_to_3():
    assert SimConfig().months_per_tick == 3


@pytest.mark.parametrize("months", [0, -1])
def test_sim_config_months_per_tick_must_be_positive(months):
    with pytest.raises(ValidationError):
        SimConfig(months_per_tick=months)


def test_demographics_model_defaults_to_artificial():
    assert ArtificialDemographicsConfig().model == "artificial"


def test_age_band_min_above_max_raises():
    with pytest.raises(ValidationError):
        AgeBandRate(min_age=5, max_age=4, rate=0.1)


def test_demographics_overlapping_bands_raise():
    with pytest.raises(ValidationError, match="overlaps"):
        ArtificialDemographicsConfig(
            fertility=[
                {"min_age": 15, "max_age": 30, "rate": 0.1},
                {"min_age": 30, "max_age": 49, "rate": 0.1},
            ]
        )


def test_demographics_overlapping_bands_within_one_sex_raise():
    with pytest.raises(ValidationError, match="mortality.F"):
        ArtificialDemographicsConfig(
            mortality={
                "F": [
                    {"min_age": 0, "max_age": 60, "rate": 0.1},
                    {"min_age": 50, "max_age": 120, "rate": 0.1},
                ]
            }
        )


def test_demographics_adjacent_bands_are_accepted():
    config = ArtificialDemographicsConfig(
        fertility=[
            {"min_age": 15, "max_age": 29, "rate": 0.1},
            {"min_age": 30, "max_age": 49, "rate": 0.1},
        ]
    )
    assert len(config.fertility) == 2


def test_demographics_unknown_key_raises():
    with pytest.raises(ValidationError):
        ArtificialDemographicsConfig(birth_rate=0.1)


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
