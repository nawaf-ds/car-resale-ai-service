from dataclasses import dataclass
from enum import StrEnum


class PriceBand(StrEnum):
    BELOW_RANGE = "BELOW_RANGE"
    WITHIN_RANGE = "WITHIN_RANGE"
    ABOVE_RANGE = "ABOVE_RANGE"


@dataclass(frozen=True, slots=True)
class Vehicle:
    make: str
    model: str
    model_year: int
    mileage_miles: float


@dataclass(frozen=True, slots=True)
class PriceAssessment:
    estimated_value_usd: float
    asking_price_usd: float
    lower_bound_usd: float
    upper_bound_usd: float
    band: PriceBand
    model_version: str

