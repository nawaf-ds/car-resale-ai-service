from __future__ import annotations

import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from used_car_assessor.adapters.model import ModelArtifactError, SklearnValueEstimator
from used_car_assessor.adapters.redis_recorder import RedisAssessmentRecorder
from used_car_assessor.api.logging import configure_logging
from used_car_assessor.api.schemas import AssessmentData, PredictRequest, SuccessEnvelope
from used_car_assessor.api.settings import Settings
from used_car_assessor.domain.entities import Vehicle
from used_car_assessor.domain.policy import PriceBandPolicy
from used_car_assessor.service.assess import AssessmentService, UnsupportedVehicleError
from used_car_assessor.service.ports import AssessmentRecorder, ValueEstimator

EstimatorLoader = Callable[[Path, Path], ValueEstimator]
RecorderFactory = Callable[[str, float], AssessmentRecorder]
TRACE_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
POLICY_NOTE = "Configurable business policy bands; not a statistical confidence interval."


def _default_estimator_loader(model_path: Path, metadata_path: Path) -> ValueEstimator:
    return SklearnValueEstimator.load(model_path, metadata_path)


def _default_recorder_factory(url: str, timeout: float) -> AssessmentRecorder:
    return RedisAssessmentRecorder(url, timeout)


def _trace_id(request: Request) -> str:
    return cast(str, request.state.trace_id)


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str | None]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "trace_id": _trace_id(request),
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            },
        },
    )


def create_app(
    settings: Settings | None = None,
    estimator_loader: EstimatorLoader = _default_estimator_loader,
    recorder_factory: RecorderFactory = _default_recorder_factory,
) -> FastAPI:
    app_settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        configure_logging(app_settings.log_level)
        logger = structlog.get_logger()
        application.state.ready = False
        application.state.startup_error = None
        application.state.recorder = None
        try:
            estimator = estimator_loader(
                app_settings.model_path, app_settings.model_metadata_path
            )
            warm_up = getattr(estimator, "warm_up", None)
            if callable(warm_up):
                warm_up()
            recorder = recorder_factory(
                app_settings.redis_url, app_settings.redis_timeout_seconds
            )
            application.state.recorder = recorder
            application.state.assessment_service = AssessmentService(
                estimator=estimator,
                policy=PriceBandPolicy(
                    lower_ratio=app_settings.policy_lower_ratio,
                    upper_ratio=app_settings.policy_upper_ratio,
                ),
                recorder=recorder,
            )
            if recorder.ping():
                application.state.ready = True
                logger.info("application_ready", model_version=estimator.model_version)
            else:
                application.state.startup_error = "supporting_service_unavailable"
                logger.error("application_not_ready", reason="supporting_service_unavailable")
        except (ModelArtifactError, OSError, ValueError) as exc:
            application.state.startup_error = "model_startup_failed"
            logger.error(
                "application_not_ready",
                reason="model_startup_failed",
                error_type=type(exc).__name__,
            )
        yield
        recorder_to_close: AssessmentRecorder | None = application.state.recorder
        if recorder_to_close is not None:
            recorder_to_close.close()
        application.state.ready = False
        logger.info("application_stopped")

    application = FastAPI(title="Used-Car Listing Price Assessment", lifespan=lifespan)

    @application.middleware("http")
    async def tracing_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied_trace = request.headers.get("X-Trace-ID", "")
        request.state.trace_id = (
            supplied_trace if TRACE_PATTERN.fullmatch(supplied_trace) else str(uuid4())
        )
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Trace-ID"] = request.state.trace_id
        structlog.get_logger().info(
            "http_request",
            trace_id=request.state.trace_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"][1:]) or None,
                "issue": error["msg"],
            }
            for error in exc.errors()
        ]
        return _error_response(
            request, 422, "VALIDATION_ERROR", "Request validation failed", details
        )

    @application.exception_handler(UnsupportedVehicleError)
    async def unsupported_vehicle(request: Request, exc: UnsupportedVehicleError) -> JSONResponse:
        return _error_response(request, 422, "UNSUPPORTED_VEHICLE", str(exc))

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        structlog.get_logger().exception(
            "request_failed", trace_id=_trace_id(request), error_type=type(exc).__name__
        )
        return _error_response(request, 500, "INTERNAL_ERROR", "An internal error occurred")

    @application.get("/health", response_model=SuccessEnvelope)
    async def health(request: Request) -> SuccessEnvelope:
        return SuccessEnvelope(trace_id=_trace_id(request), data={"status": "alive"})

    @application.get("/ready", response_model=SuccessEnvelope)
    async def ready(request: Request) -> SuccessEnvelope | JSONResponse:
        recorder = application.state.recorder
        dependencies_ready = recorder is not None and recorder.ping()
        if not application.state.ready or not dependencies_ready:
            return _error_response(
                request,
                503,
                "NOT_READY",
                "Application dependencies are not ready",
            )
        return SuccessEnvelope(trace_id=_trace_id(request), data={"status": "ready"})

    @application.post("/v1/predict", response_model=SuccessEnvelope)
    async def predict(
        payload: PredictRequest, request: Request
    ) -> SuccessEnvelope | JSONResponse:
        if not application.state.ready:
            return _error_response(request, 503, "NOT_READY", "Application is not ready")
        service = cast(AssessmentService, application.state.assessment_service)
        result = service.assess(
            Vehicle(
                make=payload.make,
                model=payload.model,
                model_year=payload.model_year,
                mileage_miles=payload.mileage_miles,
                condition=payload.condition,
            ),
            asking_price_usd=payload.asking_price_usd,
        )
        data = AssessmentData(
            estimated_value_usd=result.estimated_value_usd,
            asking_price_usd=result.asking_price_usd,
            lower_bound_usd=result.lower_bound_usd,
            upper_bound_usd=result.upper_bound_usd,
            band=result.band.value,
            model_version=result.model_version,
            policy_note=POLICY_NOTE,
        )
        return SuccessEnvelope(trace_id=_trace_id(request), data=data.model_dump())

    @application.get("/v1/stats", response_model=SuccessEnvelope)
    async def stats(request: Request) -> SuccessEnvelope | JSONResponse:
        if not application.state.ready:
            return _error_response(request, 503, "NOT_READY", "Application is not ready")
        recorder = cast(AssessmentRecorder, application.state.recorder)
        snapshot: Mapping[str, int] = recorder.snapshot()
        return SuccessEnvelope(trace_id=_trace_id(request), data=dict(snapshot))

    return application


app = create_app()
