import random

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
        pass
        # TODO

    def step(self) -> None:
        # call demographics module
        # call construction module
        # call market module
        self.clock.advance()

    def run(self) -> None:
        while self.clock.tick < self.config.sim.n_ticks:
            self.step()
