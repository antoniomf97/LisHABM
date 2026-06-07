from engine.io.scenario import Scenario, load_scenario


def test_load_scenario_returns_scenario_type(make_scenario_config):
    result = load_scenario(make_scenario_config(source="synthetic"))
    assert isinstance(result, Scenario)


def test_load_scenario_synthetic_returns_empty_lists(make_scenario_config):
    result = load_scenario(make_scenario_config(source="synthetic"))
    assert result.regions == []
    assert result.households == []
    assert result.houses == []
    assert result.constructors == []


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
