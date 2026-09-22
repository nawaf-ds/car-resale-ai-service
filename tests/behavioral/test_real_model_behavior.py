import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from used_car_assessor.adapters.model import SklearnValueEstimator
from used_car_assessor.api.app import create_app
from used_car_assessor.api.settings import Settings
from used_car_assessor.domain.entities import PriceBand, Vehicle
from used_car_assessor.domain.policy import PriceBandPolicy
from used_car_assessor.service.assess import AssessmentService
from used_car_assessor.service.ports import NullAssessmentRecorder

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.behavioral


@pytest.fixture(scope="module")
def real_service() -> AssessmentService:
    estimator = SklearnValueEstimator.load(
        ROOT / "artifacts" / "model.joblib",
        ROOT / "artifacts" / "model_metadata.json",
    )
    return AssessmentService(estimator, PriceBandPolicy(), NullAssessmentRecorder())


@pytest.fixture(scope="module")
def real_client() -> Iterator[TestClient]:
    application = create_app(
        Settings(
            environment="test",
            model_path=ROOT / "artifacts" / "model.joblib",
            model_metadata_path=ROOT / "artifacts" / "model_metadata.json",
            redis_url="redis://unused:6379/0",
        ),
        recorder_factory=lambda url, timeout: NullAssessmentRecorder(),
    )
    with TestClient(application) as client:
        yield client


def test_changing_irrelevant_identifier_does_not_affect_result(real_client: TestClient) -> None:
    payload = {
        "make": "Toyota",
        "model": "Camry",
        "model_year": 2020,
        "mileage_miles": 40_000,
        "condition": "Used",
        "asking_price_usd": 26_000,
    }

    first = real_client.post("/v1/predict", json={**payload, "listing_id": "listing-a"})
    second = real_client.post("/v1/predict", json={**payload, "listing_id": "listing-b"})

    assert first.status_code == second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


def test_increasing_asking_price_never_moves_toward_cheaper_band(
    real_service: AssessmentService,
) -> None:
    vehicle = Vehicle("Toyota", "Camry", 2020, 40_000, "Used")
    band_order = {
        PriceBand.BELOW_RANGE: 0,
        PriceBand.WITHIN_RANGE: 1,
        PriceBand.ABOVE_RANGE: 2,
    }

    results = [real_service.assess(vehicle, asking) for asking in (15_000, 26_000, 40_000)]

    assert [band_order[result.band] for result in results] == [0, 1, 2]
    assert len({result.estimated_value_usd for result in results}) == 1


def test_versioned_golden_reference(real_service: AssessmentService) -> None:
    golden: dict[str, Any] = json.loads(
        (ROOT / "tests" / "behavioral" / "golden" / "v1.json").read_text(encoding="utf-8")
    )
    case = golden["cases"][0]
    vehicle = Vehicle(**case["vehicle"])

    result = real_service.assess(vehicle, case["asking_price_usd"])
    expected = case["expected"]

    assert result.estimated_value_usd == pytest.approx(
        expected["estimated_value_usd"], abs=expected["absolute_tolerance_usd"]
    )
    assert result.lower_bound_usd == pytest.approx(
        expected["lower_bound_usd"], abs=expected["absolute_tolerance_usd"]
    )
    assert result.upper_bound_usd == pytest.approx(
        expected["upper_bound_usd"], abs=expected["absolute_tolerance_usd"]
    )
    assert result.band.value == expected["band"]
    assert result.model_version == expected["model_version"]
