from collections.abc import Mapping

import pytest

from used_car_assessor.domain.entities import PriceBand, Vehicle
from used_car_assessor.domain.policy import PriceBandPolicy
from used_car_assessor.service.assess import AssessmentService, UnsupportedVehicleError
from used_car_assessor.service.ports import NullAssessmentRecorder


class FakeEstimator:
    model_version = "fake-v1"

    def predict(self, vehicle: Vehicle) -> float:
        del vehicle
        return 20_000.0

    def supported_values(self) -> Mapping[str, frozenset[str]]:
        return {
            "make": frozenset({"Toyota"}),
            "make_model": frozenset({"Toyota::Camry"}),
        }


def test_service_orchestrates_estimation_and_policy() -> None:
    service = AssessmentService(FakeEstimator(), PriceBandPolicy(), NullAssessmentRecorder())

    result = service.assess(Vehicle("Toyota", "Camry", 2020, 35_000), 24_000)

    assert result.band is PriceBand.ABOVE_RANGE
    assert result.estimated_value_usd == 20_000
    assert result.lower_bound_usd == 17_000
    assert result.upper_bound_usd == 23_000
    assert result.model_version == "fake-v1"


@pytest.mark.parametrize(
    "vehicle",
    [Vehicle("Unknown", "Camry", 2020, 35_000), Vehicle("Toyota", "Unknown", 2020, 35_000)],
)
def test_service_rejects_unsupported_categories(vehicle: Vehicle) -> None:
    service = AssessmentService(FakeEstimator(), PriceBandPolicy(), NullAssessmentRecorder())

    with pytest.raises(UnsupportedVehicleError):
        service.assess(vehicle, 20_000)
