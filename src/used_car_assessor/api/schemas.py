from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

StrictText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    listing_id: Annotated[str, StringConstraints(min_length=1, max_length=100)] | None = None
    make: StrictText
    model: StrictText
    model_year: int = Field(ge=1990, le=2024)
    mileage_miles: float = Field(ge=100, le=300_000, allow_inf_nan=False)
    condition: Literal["Used", "Certified"]
    asking_price_usd: float = Field(ge=1_000, le=250_000, allow_inf_nan=False)


class AssessmentData(BaseModel):
    estimated_value_usd: float
    asking_price_usd: float
    lower_bound_usd: float
    upper_bound_usd: float
    band: Literal["BELOW_RANGE", "WITHIN_RANGE", "ABOVE_RANGE"]
    model_version: str
    policy_note: str


class SuccessEnvelope(BaseModel):
    trace_id: str
    data: Any


class ErrorDetail(BaseModel):
    field: str | None = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    trace_id: str
    error: ErrorBody
