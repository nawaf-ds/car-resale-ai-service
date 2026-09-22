from dataclasses import dataclass
from math import isfinite

from used_car_assessor.domain.entities import PriceBand


@dataclass(frozen=True, slots=True)
class PriceBandPolicy:
    lower_ratio: float = 0.85
    upper_ratio: float = 1.15

    def __post_init__(self) -> None:
        if not isfinite(self.lower_ratio) or not isfinite(self.upper_ratio):
            raise ValueError("Policy ratios must be finite")
        if not 0 < self.lower_ratio <= 1 <= self.upper_ratio:
            raise ValueError("Policy ratios must satisfy 0 < lower <= 1 <= upper")

    def bounds(self, estimated_value_usd: float) -> tuple[float, float]:
        if not isfinite(estimated_value_usd) or estimated_value_usd <= 0:
            raise ValueError("Estimated value must be a positive finite number")
        return (
            estimated_value_usd * self.lower_ratio,
            estimated_value_usd * self.upper_ratio,
        )

    def classify(self, asking_price_usd: float, estimated_value_usd: float) -> PriceBand:
        if not isfinite(asking_price_usd) or asking_price_usd <= 0:
            raise ValueError("Asking price must be a positive finite number")
        lower_bound, upper_bound = self.bounds(estimated_value_usd)
        if asking_price_usd < lower_bound:
            return PriceBand.BELOW_RANGE
        if asking_price_usd > upper_bound:
            return PriceBand.ABOVE_RANGE
        return PriceBand.WITHIN_RANGE

