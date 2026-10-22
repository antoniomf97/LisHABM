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
