# Used-Car Listing Price Assessment

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://github.com/nawaf-ds/car-resale-ai-service/actions/workflows/ci.yml/badge.svg)](https://github.com/nawaf-ds/car-resale-ai-service/actions/workflows/ci.yml)

## Project Context

This project was completed as part of the **SDA-AIE-113 — Software Engineering Practices for AI Systems** training program at **[SDAIA Academy](https://github.com/SDAIAAcademy)**, under the supervision of **Abdullah Khalid AlShahrani**.

The project demonstrates the practical application of software engineering practices for AI systems by building a production-style AI/ML service using clean architecture, a well-defined API contract, containerization, automated testing, CI/CD with branch protection, and secure configuration, secrets, and logging management.


## Overview

This service estimates the advertised-market value of a US used vehicle and assesses a seller's asking price. A lightweight scikit-learn model produces the independent value estimate, then a transparent domain policy returns one of three decisions:

- `BELOW_RANGE`
- `WITHIN_RANGE`
- `ABOVE_RANGE`

The asking price is never a model input. It is compared with the estimate only after prediction. The result is an assessment aid, not a guaranteed sale valuation.

## Features

### Core Functionality

- Used-vehicle value estimation from make, model, year, mileage, and condition
- Configurable price-assessment bands around the estimated value
- Strict request validation with unknown-field rejection
- Trace-aware success and error envelopes
- Redis-backed prediction statistics by decision band

### Engineering Features

- Clean `domain`, `service`, `adapters`, and `api` architecture
- Swappable model and recorder interfaces through dependency injection
- Separate liveness and real readiness endpoints
- Startup-only model loading, checksum validation, and warm-up
- Structured JSON logging correlated by trace ID
- Multi-stage, non-root Docker image under 500 MB
- Unit, integration, and real-model behavioural tests
- Automated lint, typing, architecture, secret, coverage, and container checks

## Tech Stack

| Area | Technology |
|---|---|
| API | FastAPI 0.115.12, Uvicorn 0.34.2 |
| Runtime | Python 3.11 |
| ML | scikit-learn 1.6.1, NumPy 2.2.5, Joblib 1.4.2 |
| Supporting service | Redis 7.4.1 |
| Configuration | Pydantic Settings 2.9.1 |
| Logging | Structlog 25.3.0 |
| Quality | Pytest, Ruff, mypy, import-linter, detect-secrets |
| Infrastructure | Docker, Docker Compose, GitHub Actions, GHCR |

## Quick Start

### Prerequisites

- Docker Engine or Docker Desktop with Compose
- Git, if cloning from GitHub

### Installation

```bash
git clone https://github.com/nawaf-ds/car-resale-ai-service.git
cd car-resale-ai-service
docker compose up --build --detach --wait
```

Verify the service:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/ready
```

Open the interactive API documentation at <http://localhost:8000/docs>.

Stop the stack cleanly:

```bash
docker compose down --timeout 15
```

The Compose stack includes Redis because `/v1/stats` persists real assessment counters and readiness depends on Redis availability.

## API Usage

### Create an Assessment

```bash
curl --request POST http://localhost:8000/v1/predict \
  --header "Content-Type: application/json" \
  --header "X-Trace-ID: demo-valid-001" \
  --data '{"listing_id":"seller-reference-42","make":"Toyota","model":"Camry","model_year":2020,"mileage_miles":40000,"condition":"Used","asking_price_usd":26000}'
```

Representative response:

```json
{
  "trace_id": "demo-valid-001",
  "data": {
    "estimated_value_usd": 25819.03,
    "asking_price_usd": 26000.0,
    "lower_bound_usd": 21946.18,
    "upper_bound_usd": 29691.89,
    "band": "WITHIN_RANGE",
    "model_version": "2026-09-21-v1",
    "policy_note": "Configurable business policy bands; not a statistical confidence interval."
  }
}
```

### Key Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/v1/predict` | Estimate listing value and classify asking price |
| `GET` | `/v1/stats` | Return Redis-backed assessment counters |
| `GET` | `/health` | Report process liveness |
| `GET` | `/ready` | Report model and Redis readiness |
| `GET` | `/docs` | OpenAPI/Swagger documentation |

Malformed requests return HTTP 422 in the same trace-aware envelope. Unsupported make/model combinations, invalid numerics, wrong types, out-of-range values, and unknown fields are rejected explicitly.

## Decision Policy

The default thresholds are configurable:

- Below 85% of the estimate: `BELOW_RANGE`
- From 85% through 115%, inclusive: `WITHIN_RANGE`
- Above 115% of the estimate: `ABOVE_RANGE`

These thresholds are business policy bands, not confidence intervals or model uncertainty bounds.

## Model and Data

The project uses the **US Sales Cars Dataset v2**, released on 2024-03-31 under Apache 2.0. It contains Cars.com advertised listings in USD, with mileage measured in miles. The committed snapshot has 144,867 rows; training retains 55,430 eligible, deduplicated records after documented filtering.

The training pipeline compares a median baseline, Ridge regression, and histogram gradient boosting. The selected model achieved the following results on an untouched 8,315-row test set:

| Metric | Result |
|---|---:|
| MAE | $6,317.40 |
| RMSE | $10,895.72 |
| R-squared | 0.8223 |

These metrics describe historical advertised prices, not completed sales. Listings may contain regional effects, seller strategy, stale advertisements, and unobserved vehicle condition. Full provenance and limitations are documented in `data/README.md`.

## Configuration

Copy `.env.example` to `.env` only when overrides are required. The settings layer validates configuration at startup.

| Variable | Default | Purpose |
|---|---|---|
| `UCA_ENVIRONMENT` | `development` | Runtime environment |
| `UCA_LOG_LEVEL` | `INFO` | Structured log level |
| `UCA_MODEL_PATH` | `artifacts/model.joblib` | Packaged model path |
| `UCA_MODEL_METADATA_PATH` | `artifacts/model_metadata.json` | Model metadata path |
| `UCA_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `UCA_REDIS_TIMEOUT_SECONDS` | `1.0` | Redis operation timeout |
| `UCA_POLICY_LOWER_RATIO` | `0.85` | Lower policy threshold |
| `UCA_POLICY_UPPER_RATIO` | `1.15` | Upper policy threshold |

## Local Development

Prerequisites: Python 3.11 and Redis reachable at `redis://localhost:6379/0`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev,train]"
uvicorn used_car_assessor.api.app:app --host 127.0.0.1 --port 8000 --reload
```

## Testing and Quality

```bash
make install
make lint
make test
make fast
make image
make smoke
```

Direct test commands:

```bash
python -m pytest --cov --cov-branch --cov-report=term-missing
python -m pytest -m behavioral -q
```

The verified suite contains 38 tests with 98.26% branch coverage on the configured core layers. The real-model behavioural suite checks identifier invariance, asking-price directionality, and a governed versioned golden reference.

## Architecture

```text
src/used_car_assessor/
|-- domain/      Pure entities and price-band policy
|-- service/     Assessment orchestration and Protocol ports
|-- adapters/    scikit-learn model and Redis implementations
`-- api/         FastAPI routes, schemas, lifecycle, settings, and logging
```

`import-linter` enforces the dependency direction automatically. Model and Redis clients are created and warmed only during the application lifespan, never at module import time.

## CI/CD

GitHub Actions runs the following ordered pipeline:

1. Lint, type-check, architecture validation, and secret scan
2. Tests with the branch-coverage gate
3. Docker Compose image smoke test
4. GHCR publication after a merged pull request reaches protected `main`

Published images use the full commit SHA and never the `latest` tag.

## Project Documentation

- `BENCHMARKS.md`: measured test, build, image, startup, and shutdown results
- `DECISIONS.md`: engineering decisions and rationale
- `DEMO.md`: five-minute demonstration guide
- `REQUIREMENTS.md`: complete capstone traceability matrix
- `data/README.md`: dataset provenance, license, units, and limitations

## Repository

- GitHub: <https://github.com/nawaf-ds/car-resale-ai-service>
- Issues: <https://github.com/nawaf-ds/car-resale-ai-service/issues>
