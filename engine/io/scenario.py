"""Build the initial Scenario for a run, from real or synthetic data.

This is the single place that knows real data from synthetic. Everything
downstream — the runner and the Simulator — receives a `Scenario` and is blind
to where it came from.
"""

import os
import pickle
import tempfile
from pathlib import Path
from typing import NamedTuple

import yaml

from engine.config import ScenarioConfig
from engine.core.agents import Constructor, House, Household, Region


class Scenario(NamedTuple):
    """A populated scenario — exactly the agent lists the Simulator takes."""

    regions: list[Region]
    households: list[Household]
    houses: list[House]
    constructors: list[Constructor]


def load_scenario(scenario: ScenarioConfig) -> Scenario:
    """Load the initial scenario described by ``scenario`` (from data/)."""
    if scenario.source == "real":
        return _read_real(scenario)
    return _read_synthetic(scenario)


def _read_real(scenario: ScenarioConfig) -> Scenario:
    # TODO: load the agent data files under data/<scenario.path>.
    return Scenario([], [], [], [])


def _read_synthetic(scenario: ScenarioConfig) -> Scenario:
    """Generate the scenario from the recipe YAML at ``scenario.path``.

    If ``scenario.cache`` is set and the file exists, it is unpickled instead
    and the recipe is not read. Otherwise the scenario is generated and, when
    ``cache`` is set, pickled there for the next run. This is safe because the
    recipe carries its own seed: generation is deterministic except for agent
    ids. The cache is never checked against the recipe, so after editing the
    recipe, delete or regenerate the pickle.

    The generator (``data/input/synthetic/generator.py``) itself imports
    ``Scenario`` from this module, so this import is deferred to call time:
    importing it at module load time would be a circular import (this module
    isn't fully defined yet the first time it's loaded).
    """
    cache = scenario.cache
    if cache is not None and cache.is_file():
        with cache.open("rb") as f:
            cached: Scenario = pickle.load(f)
        return cached

    from data.input.synthetic.generator import _generate_synthetic

    config = yaml.safe_load(scenario.path.read_text(encoding="utf-8"))
    generated = _generate_synthetic(config)
    if cache is not None:
        _write_cache(generated, cache)
    return generated


def _write_cache(scenario: Scenario, cache: Path) -> None:
    """Pickle ``scenario`` to ``cache`` atomically.

    Pool workers may all miss the cache and write it at the same time, so each
    writes a private temp file and renames it into place: a reader never sees
    a half-written pickle. Windows refuses the rename while another worker has
    the cache open; that worker's copy is equivalent, so ours is dropped.
    """
    cache.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=cache.parent, prefix=f"{cache.name}.")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as f:
            pickle.dump(scenario, f)
        os.replace(tmp, cache)
    except PermissionError:
        if not cache.is_file():
            raise
    finally:
        tmp.unlink(missing_ok=True)
