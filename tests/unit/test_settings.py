import pytest
from pydantic import ValidationError

from used_car_assessor.api.settings import Settings


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("environment", "unknown"),
        ("redis_timeout_seconds", 0),
        ("policy_lower_ratio", 1.1),
        ("policy_upper_ratio", 0.9),
    ],
)
def test_settings_fail_fast_on_invalid_values(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field: value})

