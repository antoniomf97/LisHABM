import random

from pydantic import BaseModel

from engine.core.agents import Constructor, House, Household, Region
from engine.core.clock import Clock


class SimConfig(BaseModel):
    n_ticks: int = 1000
    seed: int = 42


class Simulator:
    def __init__(
        self,
        config: SimConfig = SimConfig(),
        regions: list[Region] | None = None,
        households: list[Household] | None = None,
        houses: list[House] | None = None,
        constructors: list[Constructor] | None = None,
    ) -> None:
        self.config = config
        self.clock = Clock()
        self.rng = random.Random(config.seed)
        self.regions = regions or []
        self.households = households or []
        self.houses = houses or []
        self.constructors = constructors or []

    def step(self) -> None:
        # call demographics module
        # call construction module
        # call market module
        self.clock.advance()

    def run(self) -> None:
        while self.clock.tick < self.config.n_ticks:
            self.step()
