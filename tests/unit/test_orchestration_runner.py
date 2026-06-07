from pathlib import Path

import pytest

from orchestration.runner import _resolve_config, main


def test_resolve_name_only():
    assert _resolve_config("baseline") == Path("configs/baseline.yaml")


def test_resolve_name_adds_yaml_suffix():
    assert _resolve_config("baseline").suffix == ".yaml"


def test_resolve_path_with_slash():
    assert _resolve_config("configs/baseline") == Path("configs/baseline.yaml")


def test_resolve_path_already_has_extension():
    assert _resolve_config("configs/baseline.yaml") == Path("configs/baseline.yaml")


def test_resolve_backslash_path():
    result = _resolve_config("configs\\baseline")
    assert result.suffix == ".yaml"


def test_main_missing_config_exits(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "nonexistent.yaml")])
    assert exc.value.code == 2


def test_main_runs_and_returns_zero(tmp_path, minimal_yaml):
    f = tmp_path / "test.yaml"
    f.write_text(minimal_yaml)
    assert main([str(f)]) == 0
