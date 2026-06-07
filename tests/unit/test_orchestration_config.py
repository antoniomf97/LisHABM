import pytest
from pydantic import ValidationError

from orchestration.config import load_config


def test_load_config_valid(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml)
    config = load_config(f)
    assert config.run.name == "test"
    assert config.engine.scenario.source == "synthetic"


def test_load_config_run_description_defaults_to_empty(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml)
    config = load_config(f)
    assert config.run.description == ""


def test_load_config_empty_file_raises(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    with pytest.raises(ValueError, match="empty"):
        load_config(f)


def test_load_config_missing_scenario_raises(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("run:\n  name: test\nengine:\n  sim:\n    n_ticks: 10\n")
    with pytest.raises(ValidationError):
        load_config(f)


def test_load_config_invalid_source_raises(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml.replace("synthetic", "invalid_source"))
    with pytest.raises(ValidationError):
        load_config(f)


def test_load_config_invalid_every_n_ticks_raises(tmp_path, minimal_yaml):
    f = tmp_path / "config.yaml"
    f.write_text(minimal_yaml + "  output:\n    every_n_ticks: 0\n")
    with pytest.raises(ValidationError):
        load_config(f)
