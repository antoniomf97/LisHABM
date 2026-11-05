"""Multi-run scheduler.

Runs the *same* engine config N times across a process pool, varying only the
RNG seed per run so each run is an independent stochastic realization. Results
come back as a list of finished Simulators, ready for downstream averaging.
"""

import logging
from multiprocessing import Pool, cpu_count

from tqdm import tqdm

from engine.config import EngineConfig
from engine.core.simulator import Simulator

logger = logging.getLogger(__name__)


def _run_single(engine_config: EngineConfig, progress: bool = False) -> Simulator:
    """Build and run one Simulator. Top-level so it is picklable for spawn.

    On Windows (and macOS by default) multiprocessing uses the *spawn* start
    method, which re-imports this module and looks the worker up by name. A
    nested function or lambda could not be pickled, so this must stay at
    module scope.
    """
    sim = Simulator(engine_config)
    sim.run(progress=progress)
    return sim


def _config_for_run(base: EngineConfig, run_index: int) -> EngineConfig:
    """Copy ``base`` with the seed offset by ``run_index``.

    The Simulator seeds its RNG from ``config.sim.seed``. If every run shared
    one seed they would draw identical random numbers and produce identical
    output — useless to average over. Offsetting the seed per run gives
    independent realizations while keeping the whole sweep deterministic:
    the same config always yields the same set of runs.

    The seed lives in the ``sim`` sub-model, so we copy ``sim`` with the new
    seed first, then copy the engine config to point at it.
    """
    new_sim = base.sim.model_copy(update={"seed": base.sim.seed + run_index})
    return base.model_copy(update={"sim": new_sim})


def run_all(
    engine_config: EngineConfig,
    n_runs: int,
    n_workers: int | None = None,
    progress: bool = True,
) -> list[Simulator]:
    """Run ``engine_config`` ``n_runs`` times and return the finished sims.

    ``n_workers`` defaults to ``cpu_count() - 1`` (leaving one core free),
    floored at 1. A single run is executed in-process to skip pool startup
    and keep tracebacks readable when debugging.

    A tqdm bar tracks completed runs (set ``progress=False`` to silence it).
    Results use ``imap`` so the bar advances as each run finishes, while
    submission order — and therefore the per-run seed order — is preserved.
    """
    workers = n_workers if n_workers is not None else max(1, cpu_count() - 1)
    configs = [_config_for_run(engine_config, i) for i in range(n_runs)]

    if n_runs == 1:
        sim = _run_single(configs[0], progress=progress)
        _log_run_done(sim, 0, n_runs)
        return [sim]

    sims: list[Simulator] = []
    with Pool(processes=workers, initializer=_quiet_worker_logs) as pool:
        for i, sim in enumerate(
            tqdm(
                pool.imap(_run_single, configs),
                total=n_runs,
                desc="Runs",
                unit="run",
                disable=not progress,
            )
        ):
            _log_run_done(sim, i, n_runs)
            sims.append(sim)
    return sims


def _quiet_worker_logs() -> None:
    """Silence the engine's INFO logs in a pool worker.

    With many runs in parallel, every run's yearly lines would interleave on
    one terminal. Under *fork* (Linux before Python 3.14) workers inherit the
    parent's logging setup, so this is needed there; under *spawn* it keeps
    the behaviour the same. Warnings still get through.
    """
    logging.getLogger("engine").setLevel(logging.WARNING)


def _log_run_done(sim: Simulator, index: int, n_runs: int) -> None:
    logger.info(
        "run %d/%d done (seed %d): %s",
        index + 1,
        n_runs,
        sim.config.sim.seed,
        sim.summary(),
    )
