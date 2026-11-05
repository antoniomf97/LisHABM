import logging
from collections.abc import Callable

from engine.config import EngineConfig
from orchestration.scheduler.pool import _config_for_run, _quiet_worker_logs, run_all


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


def test_run_all_logs_each_finished_run_in_order(
    make_engine_config: Callable[..., EngineConfig], caplog
) -> None:
    caplog.set_level(logging.INFO, logger="orchestration.scheduler.pool")
    run_all(make_engine_config(seed=42), n_runs=3, n_workers=2, progress=False)
    done = [r.getMessage().split(":")[0] for r in caplog.records]
    assert done == [
        "run 1/3 done (seed 42)",
        "run 2/3 done (seed 43)",
        "run 3/3 done (seed 44)",
    ]


def test_quiet_worker_logs_silences_engine_info() -> None:
    engine_logger = logging.getLogger("engine")
    old_level = engine_logger.level
    try:
        _quiet_worker_logs()
        sim_logger = logging.getLogger("engine.core.simulator")
        assert not sim_logger.isEnabledFor(logging.INFO)
        assert sim_logger.isEnabledFor(logging.WARNING)
    finally:
        engine_logger.setLevel(old_level)
