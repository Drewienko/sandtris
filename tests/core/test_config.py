import pytest

from sandtris.core.config import GameConfig


def test_config_derives_standard_grid_from_scale() -> None:
    config = GameConfig(scale=8)

    assert config.width == 80
    assert config.height == 160


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("scale", 0),
        ("fps", 0),
        ("fall_delay", 0),
        ("fast_fall_delay", 0),
    ],
)
def test_config_rejects_non_positive_values(
    field_name: str,
    value: int,
) -> None:
    kwargs = {field_name: value}

    with pytest.raises(ValueError):
        GameConfig(**kwargs)
