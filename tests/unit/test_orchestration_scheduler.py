from collections.abc import Callable

from engine.config import EngineConfig
from orchestration.scheduler.pool import _config_for_run, run_all


def test_config_for_run_offsets_seed(
    make_engine_config: Callable[..., EngineConfig],
) -> None:
    base = make_engine_config(seed=100)
    assert _config_for_run(base, 0).sim.seed == 100
    assert _config_for_run(base, 3).sim.seed == 103


def test_config_for_run_does_not_mutate_base(
    make_engine_config: Callable[..., EngineConfig],
) -> None:
    base = make_engine_config(seed=100)
    _config_for_run(base, 5)
    assert base.sim.seed == 100


def test_run_all_single_run_in_process(
    make_engine_config: Callable[..., EngineConfig],
) -> None:
    sims = run_all(make_engine_config(seed=42), n_runs=1)
    assert len(sims) == 1
    assert sims[0].config.sim.seed == 42


def test_run_all_returns_one_sim_per_run(
    make_engine_config: Callable[..., EngineConfig],
) -> None:
    sims = run_all(make_engine_config(seed=42), n_runs=3, n_workers=2)
    assert len(sims) == 3


def test_run_all_derives_distinct_seeds(
    make_engine_config: Callable[..., EngineConfig],
) -> None:
    sims = run_all(make_engine_config(seed=42), n_runs=3, n_workers=2)
    assert [s.config.sim.seed for s in sims] == [42, 43, 44]
