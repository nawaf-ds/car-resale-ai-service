from collections.abc import Mapping
from pathlib import Path

from fastapi.testclient import TestClient

from used_car_assessor.adapters.model import ModelArtifactError
from used_car_assessor.api.app import create_app
from used_car_assessor.api.settings import Settings
from used_car_assessor.domain.entities import Vehicle


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

    def warm_up(self) -> None:
        return None


class FakeRecorder:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.closed = False
        self.counts = {"total": 0, "below_range": 0, "within_range": 0, "above_range": 0}

    def record(self, band: str) -> None:
        self.counts["total"] += 1
        self.counts[band.lower()] += 1

    def ping(self) -> bool:
        return self.available

    def snapshot(self) -> Mapping[str, int]:
        return self.counts

    def close(self) -> None:
        self.closed = True


class FailingRecorder(FakeRecorder):
    def record(self, band: str) -> None:
        del band
        raise RuntimeError("sensitive internal detail")


def settings() -> Settings:
    return Settings(
        environment="test",
        model_path=Path("unused-model"),
        model_metadata_path=Path("unused-metadata"),
        redis_url="redis://unused:6379/0",
    )


def make_client(
    recorder: FakeRecorder | None = None, *, raise_server_exceptions: bool = True
) -> tuple[TestClient, FakeRecorder]:
    active_recorder = recorder or FakeRecorder()
    app = create_app(
        settings(),
        estimator_loader=lambda model_path, metadata_path: FakeEstimator(),
        recorder_factory=lambda url, timeout: active_recorder,
    )
    return TestClient(app, raise_server_exceptions=raise_server_exceptions), active_recorder


VALID_REQUEST = {
    "listing_id": "listing-123",
    "make": "Toyota",
    "model": "Camry",
    "model_year": 2020,
    "mileage_miles": 40_000,
    "condition": "Used",
    "asking_price_usd": 20_000,
}


def test_health_readiness_prediction_stats_and_shutdown() -> None:
    client, recorder = make_client()
    with client:
        health = client.get("/health", headers={"X-Trace-ID": "trace-test"})
        ready = client.get("/ready")
        prediction = client.post("/v1/predict", json=VALID_REQUEST)
        stats = client.get("/v1/stats")

        assert health.status_code == 200
        assert health.json() == {"trace_id": "trace-test", "data": {"status": "alive"}}
        assert health.headers["X-Trace-ID"] == "trace-test"
        assert ready.status_code == 200
        assert prediction.status_code == 200
        assert prediction.json()["data"]["band"] == "WITHIN_RANGE"
        assert "confidence interval" in prediction.json()["data"]["policy_note"]
        assert stats.json()["data"]["total"] == 1
        assert stats.json()["data"]["within_range"] == 1
    assert recorder.closed is True


def test_unknown_fields_and_invalid_values_use_error_envelope() -> None:
    client, _ = make_client()
    invalid = {**VALID_REQUEST, "asking_price_usd": "NaN", "unknown": "value"}
    with client:
        response = client.post("/v1/predict", json=invalid)

    assert response.status_code == 422
    body = response.json()
    assert body["trace_id"]
    assert body["error"]["code"] == "VALIDATION_ERROR"
    fields = {detail["field"] for detail in body["error"]["details"]}
    assert fields == {"asking_price_usd", "unknown"}


def test_unsupported_category_is_explicit() -> None:
    client, _ = make_client()
    with client:
        response = client.post("/v1/predict", json={**VALID_REQUEST, "make": "Unknown"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_VEHICLE"


def test_liveness_remains_up_when_supporting_service_is_down() -> None:
    client, _ = make_client(FakeRecorder(available=False))
    with client:
        assert client.get("/health").status_code == 200
        ready = client.get("/ready")
        prediction = client.post("/v1/predict", json=VALID_REQUEST)

    assert ready.status_code == 503
    assert ready.json()["error"]["code"] == "NOT_READY"
    assert prediction.status_code == 503


def test_model_startup_failure_reports_not_ready() -> None:
    app = create_app(
        settings(),
        estimator_loader=lambda model_path, metadata_path: (_ for _ in ()).throw(
            ModelArtifactError("broken")
        ),
        recorder_factory=lambda url, timeout: FakeRecorder(),
    )
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503


def test_internal_exception_uses_safe_error_envelope() -> None:
    client, _ = make_client(FailingRecorder(), raise_server_exceptions=False)
    with client:
        response = client.post("/v1/predict", json=VALID_REQUEST)

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "An internal error occurred",
        "details": [],
    }
    assert "sensitive internal detail" not in response.text
