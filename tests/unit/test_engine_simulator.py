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
