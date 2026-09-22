import pytest

from used_car_assessor.domain.entities import PriceBand
from used_car_assessor.domain.policy import PriceBandPolicy


@pytest.mark.parametrize(
    ("asking_price", "expected"),
    [
        (8_499.99, PriceBand.BELOW_RANGE),
        (8_500.00, PriceBand.WITHIN_RANGE),
        (10_000.00, PriceBand.WITHIN_RANGE),
        (11_500.00, PriceBand.WITHIN_RANGE),
        (11_500.01, PriceBand.ABOVE_RANGE),
    ],
)
def test_policy_boundaries(asking_price: float, expected: PriceBand) -> None:
    assert PriceBandPolicy().classify(asking_price, 10_000) is expected


@pytest.mark.parametrize(
    ("lower", "upper"),
    [(0, 1.1), (1.1, 1.2), (0.8, 0.9), (float("nan"), 1.1)],
)
def test_policy_rejects_invalid_ratios(lower: float, upper: float) -> None:
    with pytest.raises(ValueError):
        PriceBandPolicy(lower_ratio=lower, upper_ratio=upper)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_policy_rejects_invalid_estimate(value: float) -> None:
    with pytest.raises(ValueError):
        PriceBandPolicy().bounds(value)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_policy_rejects_invalid_asking_price(value: float) -> None:
    with pytest.raises(ValueError):
        PriceBandPolicy().classify(value, 10_000)

