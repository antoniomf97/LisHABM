import random

from tqdm import tqdm

from engine.config import EngineConfig, ScenarioConfig
from engine.core.clock import Clock
from engine.io.scenario import load_scenario


class Simulator:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.clock = Clock()
        self.rng = random.Random(config.sim.seed)
        self.initialize_scenario(config.scenario)

    def initialize_scenario(self, config: ScenarioConfig) -> None:
        load_scenario(config)

        # print({name: len(items) for name, items in scenario._asdict().items()})
        pass
        # TODO

    def step(self) -> None:
        # call demographics module
        # call construction module
        # call market module
        self.clock.advance()

    def run(self, progress: bool = True) -> None:
        remaining = self.config.sim.n_ticks - self.clock.tick
        for _ in tqdm(
            range(remaining), desc="Ticks", unit="tick", disable=not progress
        ):
            self.step()
