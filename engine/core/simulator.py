import logging
import random

from tqdm import tqdm

from engine.config import EngineConfig, ScenarioConfig
from engine.core.agents import Household
from engine.core.clock import Clock
from engine.io.scenario import load_scenario

logger = logging.getLogger(__name__)


class Simulator:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.clock = Clock()
        self.rng = random.Random(config.sim.seed)
        self.households: list[Household] = []
        self.initialize_scenario(config.scenario)

    def initialize_scenario(self, config: ScenarioConfig) -> None:
        scenario = load_scenario(config)
        self.households = scenario.households
        logger.info(
            "scenario loaded: %s",
            " ".join(
                f"{name}={len(items)}" for name, items in scenario._asdict().items()
            ),
        )
        # TODO

    def summary(self) -> str:
        """One-line population summary, for logs."""
        persons = [p for hh in self.households for p in hh.members]
        mean_age = (
            f"{sum(p.age for p in persons) / len(persons):.1f}" if persons else "n/a"
        )
        return (
            f"households={len(self.households)} persons={len(persons)} "
            f"mean_age={mean_age}"
        )

    def step(self) -> None:
        # call demographics module
        # call construction module
        # call market module
        self.clock.advance()
        self._log_year_end()

    def _log_year_end(self) -> None:
        """Log a summary on the step that completes a simulated year.

        Year ``n`` ends once ``n * 12`` months have elapsed, with
        ``tick * months_per_tick`` months elapsed after ``tick`` steps. A tick
        longer than a year logs only the latest year it completes.
        """
        tick, months = self.clock.tick, self.config.sim.months_per_tick
        year = tick * months // 12
        if year > (tick - 1) * months // 12 and logger.isEnabledFor(logging.INFO):
            logger.info("year %d (tick %d): %s", year, tick, self.summary())

    def run(self, progress: bool = True) -> None:
        remaining = self.config.sim.n_ticks - self.clock.tick
        for _ in tqdm(
            range(remaining), desc="Ticks", unit="tick", disable=not progress
        ):
            self.step()
