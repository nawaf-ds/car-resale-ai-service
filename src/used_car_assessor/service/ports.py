from collections.abc import Mapping
from typing import Protocol

from used_car_assessor.domain.entities import Vehicle


class ValueEstimator(Protocol):
    @property
    def model_version(self) -> str: ...

    def predict(self, vehicle: Vehicle) -> float: ...

    def supported_values(self) -> Mapping[str, frozenset[str]]: ...


class AssessmentRecorder(Protocol):
    def record(self, band: str) -> None: ...

    def ping(self) -> bool: ...

    def close(self) -> None: ...


class NullAssessmentRecorder:
    def record(self, band: str) -> None:
        del band

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        return None

