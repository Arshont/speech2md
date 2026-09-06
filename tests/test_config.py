import json

import pytest

from speech2md import config as config_mod
from speech2md.config import load_config, save_config


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    path = tmp_path / "speech2md" / "config.json"
    monkeypatch.setattr(config_mod, "config_path", lambda: path)
    return path


def test_load_missing_config(isolated_config):
    assert load_config() == {}


def test_save_and_load_roundtrip(isolated_config):
    save_config({"model": "large-v3-turbo"})
    assert load_config() == {"model": "large-v3-turbo"}


def test_save_merges_existing(isolated_config):
    save_config({"model": "small"})
    save_config({"language": "ru"})
    assert load_config() == {"model": "small", "language": "ru"}


def test_load_corrupt_config(isolated_config):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text("{not json", encoding="utf-8")
    assert load_config() == {}


def test_load_non_dict_config(isolated_config):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text(json.dumps(["list"]), encoding="utf-8")
    assert load_config() == {}
