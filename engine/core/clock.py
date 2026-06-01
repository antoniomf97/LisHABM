from dataclasses import dataclass


@dataclass
class Clock:
    tick: int = 0

    def advance(self) -> None:
        self.tick += 1
