from dataclasses import dataclass

from used_car_assessor.domain.entities import PriceAssessment, Vehicle
from used_car_assessor.domain.policy import PriceBandPolicy
from used_car_assessor.service.ports import AssessmentRecorder, ValueEstimator


class UnsupportedVehicleError(ValueError):
    pass


@dataclass(slots=True)
class AssessmentService:
    estimator: ValueEstimator
    policy: PriceBandPolicy
    recorder: AssessmentRecorder

    def assess(self, vehicle: Vehicle, asking_price_usd: float) -> PriceAssessment:
        self._validate_supported(vehicle)
        estimated_value = self.estimator.predict(vehicle)
        lower_bound, upper_bound = self.policy.bounds(estimated_value)
        band = self.policy.classify(asking_price_usd, estimated_value)
        self.recorder.record(band.value)
        return PriceAssessment(
            estimated_value_usd=round(estimated_value, 2),
            asking_price_usd=round(asking_price_usd, 2),
            lower_bound_usd=round(lower_bound, 2),
            upper_bound_usd=round(upper_bound, 2),
            band=band,
            model_version=self.estimator.model_version,
        )

    def _validate_supported(self, vehicle: Vehicle) -> None:
        supported = self.estimator.supported_values()
        if vehicle.make not in supported["make"]:
            raise UnsupportedVehicleError(f"Unsupported make: {vehicle.make}")
        model_key = f"{vehicle.make}::{vehicle.model}"
        if model_key not in supported["make_model"]:
            raise UnsupportedVehicleError(
                f"Unsupported model '{vehicle.model}' for make '{vehicle.make}'"
            )

