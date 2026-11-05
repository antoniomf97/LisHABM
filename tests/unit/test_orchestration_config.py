import pytest
from pydantic import ValidationError

from orchestration.config import load_config


def test_load_config_valid(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml)
    config = load_config(f)
    assert config.runs.name == "test"
    assert config.engine.scenario.source == "synthetic"


def test_load_config_empty_file_raises(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    with pytest.raises(ValueError, match="empty"):
        load_config(f)


def test_load_config_missing_scenario_raises(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("runs:\n  name: test\nengine:\n  sim:\n    n_ticks: 10\n")
    with pytest.raises(ValidationError):
        load_config(f)


def test_load_config_invalid_source_raises(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml.replace("synthetic", "invalid_source"))
    with pytest.raises(ValidationError):
        load_config(f)


def test_load_config_module_name_resolves_to_file_next_to_config(
    tmp_path, minimal_yaml
):
    (tmp_path / "demographics").mkdir()
    (tmp_path / "demographics" / "artificial.yaml").write_text("adult_age: 21\n")
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml + "  demographics: artificial\n")
    assert load_config(f).engine.demographics.adult_age == 21


def test_load_config_inline_module_mapping_still_works(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml + "  demographics:\n    adult_age: 21\n")
    assert load_config(f).engine.demographics.adult_age == 21


def test_load_config_missing_module_file_names_path(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml + "  demographics: nope\n")
    expected = tmp_path / "demographics" / "nope.yaml"
    with pytest.raises(FileNotFoundError) as exc:
        load_config(f)
    assert "demographics" in str(exc.value)
    assert "'nope'" in str(exc.value)
    assert str(expected) in str(exc.value)


def test_load_config_empty_module_file_raises(tmp_path, minimal_yaml):
    (tmp_path / "demographics").mkdir()
    (tmp_path / "demographics" / "artificial.yaml").write_text("")
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml + "  demographics: artificial\n")
    with pytest.raises(ValueError, match="empty"):
        load_config(f)


def test_load_config_invalid_every_n_ticks_raises(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml + "  output:\n    every_n_ticks: 0\n")
    with pytest.raises(ValidationError):
        load_config(f)
