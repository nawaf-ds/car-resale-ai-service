from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import joblib

from used_car_assessor.domain.entities import Vehicle


class ModelArtifactError(RuntimeError):
    pass


class SklearnValueEstimator:
    def __init__(self, pipeline: Any, metadata: Mapping[str, Any]) -> None:
        self._pipeline = pipeline
        self._metadata = metadata

    @classmethod
    def load(cls, model_path: Path, metadata_path: Path) -> SklearnValueEstimator:
        if not model_path.is_file() or not metadata_path.is_file():
            raise ModelArtifactError("Model artifact or metadata file is missing")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected_hash = metadata.get("model_sha256")
        actual_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
        if not expected_hash or actual_hash != expected_hash:
            raise ModelArtifactError("Model artifact checksum does not match metadata")
        pipeline = joblib.load(model_path)
        return cls(pipeline, metadata)

    @property
    def model_version(self) -> str:
        return cast(str, self._metadata["model_version"])

    def predict(self, vehicle: Vehicle) -> float:
        row = [
            [
                vehicle.make,
                vehicle.model,
                vehicle.model_year,
                vehicle.mileage_miles,
                vehicle.condition,
            ]
        ]
        prediction = float(self._pipeline.predict(row)[0])
        if prediction <= 0:
            raise ModelArtifactError("Model returned a non-positive estimate")
        return prediction

    def supported_values(self) -> Mapping[str, frozenset[str]]:
        values = self._metadata["supported_values"]
        return {
            "make": frozenset(values["make"]),
            "make_model": frozenset(values["make_model"]),
        }

    def warm_up(self) -> None:
        supported = self.supported_values()
        first_make_model = sorted(supported["make_model"])[0]
        make, model = first_make_model.split("::", maxsplit=1)
        self.predict(Vehicle(make, model, 2020, 40_000, "Used"))
