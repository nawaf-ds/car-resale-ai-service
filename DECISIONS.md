# Engineering Decisions

## 1. Predict value without the seller's asking price

The regression features are make, model, model year, mileage in miles, and listing condition. Asking price is deliberately excluded and metadata asserts `asking_price_is_feature: false`. This prevents the estimate from simply echoing the value it is meant to assess. Asking price enters only the pure domain policy after prediction.

## 2. Treat ranges as explicit policy, not uncertainty

The default 85%-115% band is a configurable business rule with inclusive boundaries. The API labels it accordingly. The model does not calculate calibrated prediction intervals, so describing these thresholds as statistical confidence would be misleading.

## 3. Select a small histogram-gradient model by validation MAE

A median baseline, one-hot Ridge model, and histogram gradient boosting model were compared on the same validation split. Histogram gradient boosting produced the lowest validation MAE and materially outperformed the baseline, while keeping the serialized pipeline to roughly 280 KB and CPU training practical. The untouched test set was evaluated only after selection/refit.

## 4. Pin a redistributable snapshot and disclose provenance gaps

The project commits the exact Apache-2.0 Kaggle version-2 snapshot and verifies its SHA-256 before training. This avoids silent upstream drift. The publisher documents Cars.com scraping, US dollars, and mileage in miles but does not state an exact scrape window; the project records that limitation instead of inventing dates. Advertised prices are explicitly not completed-sale prices.

## 5. Use Redis for a real operational extension

Redis persists aggregate assessment counts exposed by `/v1/stats`. It adds demonstrable functionality and readiness value, unlike an unused sidecar. Compose gates API startup on Redis health, `/ready` checks Redis at request time, and failure tests keep `/health` live while readiness returns 503.

## 6. Keep startup effects inside the application lifespan

Importing the API module creates configuration and route definitions only. Model loading, checksum validation, warm-up, and Redis connection happen during FastAPI startup. Shutdown closes Redis and clears readiness. This makes import-time tests deterministic and supports clean container termination.

