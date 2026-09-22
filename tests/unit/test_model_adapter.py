import hashlib
import json
from pathlib import Path

import joblib
import pytest

from used_car_assessor.adapters.model import ModelArtifactError, SklearnValueEstimator
from used_car_assessor.domain.entities import Vehicle


class FakePipeline:
    def predict(self, rows: list[list[object]]) -> list[float]:
        assert rows == [["Toyota", "Camry", 2020, 40_000, "Used"]]
        return [21_500.0]


def write_artifact(tmp_path: Path) -> tuple[Path, Path]:
    model_path = tmp_path / "model.joblib"
    metadata_path = tmp_path / "metadata.json"
    joblib.dump(FakePipeline(), model_path)
    metadata = {
        "model_version": "test-v1",
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "supported_values": {
            "make": ["Toyota"],
            "make_model": ["Toyota::Camry"],
        },
    }
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return model_path, metadata_path


def test_load_predict_and_warm_up(tmp_path: Path) -> None:
    estimator = SklearnValueEstimator.load(*write_artifact(tmp_path))

    assert estimator.model_version == "test-v1"
    assert estimator.predict(Vehicle("Toyota", "Camry", 2020, 40_000, "Used")) == 21_500
    assert estimator.supported_values()["make"] == {"Toyota"}
    estimator.warm_up()


def test_load_rejects_missing_artifacts(tmp_path: Path) -> None:
    with pytest.raises(ModelArtifactError, match="missing"):
        SklearnValueEstimator.load(tmp_path / "missing", tmp_path / "metadata")


def test_load_rejects_checksum_mismatch(tmp_path: Path) -> None:
    model_path, metadata_path = write_artifact(tmp_path)
    metadata_path.write_text(
        json.dumps({"model_sha256": "wrong", "model_version": "x"}), encoding="utf-8"
    )

    with pytest.raises(ModelArtifactError, match="checksum"):
        SklearnValueEstimator.load(model_path, metadata_path)


def test_predict_rejects_non_positive_value() -> None:
    class BrokenPipeline:
        def predict(self, rows: list[list[object]]) -> list[float]:
            del rows
            return [-1]

    estimator = SklearnValueEstimator(
        BrokenPipeline(),
        {
            "model_version": "broken",
            "supported_values": {"make": ["Toyota"], "make_model": ["Toyota::Camry"]},
        },
    )

    with pytest.raises(ModelArtifactError, match="non-positive"):
        estimator.predict(Vehicle("Toyota", "Camry", 2020, 40_000, "Used"))
