import json
from pathlib import Path

import pytest

from sandtris.runners.pygame_runner import load_persistent_data, save_persistent_data


def test_round_trip_list(tmp_path: Path) -> None:
    path = tmp_path / "scores.json"
    data = [{"score": 100}, {"score": 50}]
    save_persistent_data("key", path, data)
    loaded = load_persistent_data("key", path)
    assert loaded == data


def test_round_trip_dict(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    data = {"theme_name": "Egyptian", "scale": 4}
    save_persistent_data("key", path, data)
    loaded = load_persistent_data("key", path)
    assert loaded == data


def test_load_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.json"
    result = load_persistent_data("key", path)
    assert result == {}


def test_load_corrupt_json_returns_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not valid json {{{{")
    result = load_persistent_data("key", path)
    assert result == {}


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "a" / "b" / "c" / "data.json"
    save_persistent_data("key", path, {"x": 1})
    assert path.exists()
    assert json.loads(path.read_text()) == {"x": 1}
