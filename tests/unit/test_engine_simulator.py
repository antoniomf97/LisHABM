import logging

import pytest

from engine.config import SimConfig
from engine.core.simulator import Simulator


def test_simulator_clock_starts_at_zero(make_engine_config):
    sim = Simulator(make_engine_config())
    assert sim.clock.tick == 0


def test_step_advances_clock_by_one(make_engine_config):
    sim = Simulator(make_engine_config())
    sim.step()
    assert sim.clock.tick == 1


def test_run_advances_clock_to_n_ticks(make_engine_config):
    sim = Simulator(make_engine_config(n_ticks=5))
    sim.run()
    assert sim.clock.tick == 5


def test_run_without_progress_advances_clock_to_n_ticks(make_engine_config):
    sim = Simulator(make_engine_config(n_ticks=5))
    sim.run(progress=False)
    assert sim.clock.tick == 5


def test_run_zero_ticks_does_not_advance(make_engine_config):
    sim = Simulator(make_engine_config(n_ticks=0))
    sim.run()
    assert sim.clock.tick == 0


def test_simulator_rng_is_seeded(make_engine_config):
    sim_a = Simulator(make_engine_config(seed=42))
    sim_b = Simulator(make_engine_config(seed=42))
    assert sim_a.rng.random() == sim_b.rng.random()


def test_simulator_different_seeds_differ(make_engine_config):
    sim_a = Simulator(make_engine_config(seed=1))
    sim_b = Simulator(make_engine_config(seed=2))
    assert sim_a.rng.random() != sim_b.rng.random()


def test_simulator_keeps_scenario_households(
    make_engine_config, make_scenario_config, synthetic_recipe_path
):
    scenario = make_scenario_config(source="synthetic", path=synthetic_recipe_path)
    sim = Simulator(make_engine_config(scenario=scenario))
    assert len(sim.households) == 2


def test_summary_counts_households_and_persons(
    make_engine_config, make_scenario_config, synthetic_recipe_path
):
    scenario = make_scenario_config(source="synthetic", path=synthetic_recipe_path)
    sim = Simulator(make_engine_config(scenario=scenario))
    assert sim.summary().startswith("households=2 persons=2 mean_age=")


def test_summary_of_empty_population(make_engine_config):
    sim = Simulator(make_engine_config())
    assert sim.summary() == "households=0 persons=0 mean_age=n/a"


@pytest.mark.parametrize(
    ("months_per_tick", "n_ticks", "expected"),
    [
        (3, 8, ["year 1 (tick 4)", "year 2 (tick 8)"]),
        (5, 5, ["year 1 (tick 3)", "year 2 (tick 5)"]),
        (12, 2, ["year 1 (tick 1)", "year 2 (tick 2)"]),
        (24, 2, ["year 2 (tick 1)", "year 4 (tick 2)"]),
    ],
)
def test_run_logs_once_per_simulated_year(
    make_engine_config, caplog, months_per_tick, n_ticks, expected
):
    sim_config = SimConfig(n_ticks=n_ticks, months_per_tick=months_per_tick)
    sim = Simulator(make_engine_config(sim=sim_config))
    caplog.set_level(logging.INFO, logger="engine.core.simulator")
    sim.run(progress=False)
    year_lines = [
        r.getMessage().split(":")[0]
        for r in caplog.records
        if r.getMessage().startswith("year ")
    ]
    assert year_lines == expected
