# Used-Car Listing Price Assessment

A production-oriented SDA-AIE-113 capstone service that estimates a US used vehicle's advertised listing value and applies explicit policy bands to classify the seller's asking price as `BELOW_RANGE`, `WITHIN_RANGE`, or `ABOVE_RANGE`.

The seller's asking price is never a model feature. It is compared with the independently estimated listing value only after prediction.

## Quick start (under 10 minutes)

### Docker Compose

Prerequisites: Docker Engine/Desktop with Compose.

```bash
docker compose up --build --detach --wait
curl --fail http://localhost:8000/ready
```

Stop cleanly with:

```bash
docker compose down --timeout 15
```

The stack contains the API and Redis 7.4.1. Redis provides durable assessment counters for the `/v1/stats` extension and is an essential readiness dependency rather than an unused checklist container.

### Local Python

Prerequisites: Python 3.11 and Redis reachable at `redis://localhost:6379/0`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev,train]"
uvicorn used_car_assessor.api.app:app --host 127.0.0.1 --port 8000
```

Copy `.env.example` to `.env` only when configuration overrides are needed. It contains placeholders/defaults and no credentials.

## API

### Valid prediction

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

### Malformed prediction

```bash
curl --request POST http://localhost:8000/v1/predict \
  --header "Content-Type: application/json" \
  --data '{"make":"Toyota","model":"Camry","model_year":2035,"mileage_miles":"unknown","condition":"Used","asking_price_usd":26000,"extra":"rejected"}'
```

This returns HTTP 422 with the same trace-aware envelope. Unknown fields, wrong types, non-finite values, out-of-range values, and unsupported make/model combinations are rejected explicitly.

### Operational endpoints

- `GET /health`: process liveness only.
- `GET /ready`: model and Redis readiness; returns HTTP 503 if either is unavailable.
- `GET /v1/stats`: Redis-backed counts by policy band (tested extension).

## Model and data

The source is the **US Sales Cars Dataset v2**, released 2024-03-31 under Apache 2.0. It contains Cars.com advertised listings in USD with mileage in miles. The exact scrape window is not documented by the publisher; this is recorded as a provenance limitation in `data/README.md` rather than inferred.

Training starts with 144,867 rows, selects used/certified records, removes incomplete and exact duplicate rows, applies plausibility filters, and retains 55,430 rows. Data is split before learned preprocessing into train (38,801), validation (8,314), and untouched test (8,315) partitions.

Compared validation models:

| Model | Validation MAE | Validation RMSE | Validation R² |
|---|---:|---:|---:|
| Median baseline | $17,065.47 | $26,276.19 | -0.0399 |
| Ridge | $7,923.53 | $13,252.49 | 0.7355 |
| Histogram gradient boosting | $6,607.46 | $11,424.54 | 0.8034 |

The selected histogram gradient boosting pipeline achieved **MAE $6,317.40**, **RMSE $10,895.72**, and **R² 0.8223** on the untouched test set. These are actual results from `reports/model_evaluation.json`.

These metrics describe performance on historical advertised listing prices, not completed sales. The data can contain listing bias, regional effects, stale advertisements, unobserved vehicle condition, and seller strategy. The service is an assessment aid, not a valuation guarantee.

## Decision policy

Default policy bands are configurable with `UCA_POLICY_LOWER_RATIO` and `UCA_POLICY_UPPER_RATIO`:

- asking price below 85% of estimate: `BELOW_RANGE`
- asking price from 85% through 115%, inclusive: `WITHIN_RANGE`
- asking price above 115%: `ABOVE_RANGE`

These are transparent business policy bands, not confidence intervals and not model uncertainty bounds.

## Quality commands

```bash
make install
make lint
make test
make fast
make image
make smoke
```

Equivalent direct test command:

```bash
python -m pytest --cov --cov-branch --cov-report=term-missing
```

The behavioural suite uses the real packaged model:

```bash
python -m pytest -m behavioral -q
```

The golden fixture is governed by `tests/behavioral/golden/README.md`; never regenerate it merely to make a failing test pass.

## Architecture

- `domain`: pure vehicle, result, and policy rules.
- `service`: assessment orchestration plus `Protocol` ports.
- `adapters`: scikit-learn artifact and Redis implementations.
- `api`: FastAPI schemas, lifecycle, envelopes, trace/logging, and settings.

`import-linter` enforces this dependency direction automatically. The model and Redis clients are created and warmed only inside the application lifespan, never during module import.

See `DECISIONS.md`, `BENCHMARKS.md`, `DEMO.md`, and `REQUIREMENTS.md` for rationale, measured evidence, presentation steps, and the complete acceptance audit.
