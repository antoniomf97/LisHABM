import pickle
from pathlib import Path

import engine.io.scenario as scenario_module
from engine.io.scenario import Scenario, load_scenario


def test_load_scenario_returns_scenario_type(
    make_scenario_config, synthetic_recipe_path
):
    result = load_scenario(
        make_scenario_config(source="synthetic", path=synthetic_recipe_path)
    )
    assert isinstance(result, Scenario)


def test_load_scenario_synthetic_matches_recipe_counts(
    make_scenario_config, synthetic_recipe_path
):
    result = load_scenario(
        make_scenario_config(source="synthetic", path=synthetic_recipe_path)
    )
    assert len(result.regions) == 2
    assert len(result.households) == 2
    assert len(result.houses) == 2
    assert len(result.constructors) == 1


def test_load_scenario_synthetic_is_deterministic_for_same_recipe(
    make_scenario_config, synthetic_recipe_path
):
    config = make_scenario_config(source="synthetic", path=synthetic_recipe_path)
    first = load_scenario(config)
    second = load_scenario(config)

    assert [h.evaluation_price for h in first.houses] == [
        h.evaluation_price for h in second.houses
    ]
    assert [hh.capital for hh in first.households] == [
        hh.capital for hh in second.households
    ]


def test_load_scenario_synthetic_writes_missing_cache(
    make_scenario_config, synthetic_recipe_path, tmp_path
):
    cache = tmp_path / "scenarios" / "cached.pkl"
    config = make_scenario_config(
        source="synthetic", path=synthetic_recipe_path, cache=cache
    )
    generated = load_scenario(config)

    with cache.open("rb") as f:
        cached = pickle.load(f)
    assert [h.evaluation_price for h in cached.houses] == [
        h.evaluation_price for h in generated.houses
    ]
    assert list(cache.parent.iterdir()) == [cache]  # no temp file left behind


def test_load_scenario_synthetic_loads_existing_cache(make_scenario_config, tmp_path):
    cache = tmp_path / "cached.pkl"
    with cache.open("wb") as f:
        pickle.dump(Scenario([], [], [], []), f)
    # The recipe does not exist: loading must not touch it.
    config = make_scenario_config(
        source="synthetic", path=tmp_path / "missing.yaml", cache=cache
    )
    assert load_scenario(config) == Scenario([], [], [], [])


def test_load_scenario_synthetic_tolerates_cache_locked_by_other_worker(
    make_scenario_config, synthetic_recipe_path, tmp_path, monkeypatch
):
    # Simulate Windows refusing the rename because another worker wrote the
    # cache and still has it open.
    cache = tmp_path / "cached.pkl"

    def locked_replace(src, dst):
        Path(dst).write_bytes(b"written by another worker")
        raise PermissionError

    monkeypatch.setattr(scenario_module.os, "replace", locked_replace)
    config = make_scenario_config(
        source="synthetic", path=synthetic_recipe_path, cache=cache
    )
    assert len(load_scenario(config).houses) == 2
    assert cache.read_bytes() == b"written by another worker"
    assert list(tmp_path.glob("cached.pkl.*")) == []


def test_load_scenario_real_returns_empty_lists(make_scenario_config):
    result = load_scenario(make_scenario_config(source="real"))
    assert result.regions == []
    assert result.households == []
    assert result.houses == []
    assert result.constructors == []


def test_scenario_supports_positional_access():
    scenario = Scenario([], [], [], [])
    regions, households, houses, constructors = scenario
    assert regions == []
    assert constructors == []
