# Benchmarks

Measured on 2026-09-21 on Windows 10 build 19045 (x64), Python 3.11.9, an Intel64 Family 6 Model 142 processor (8 logical processors), and 7.6 GB RAM. Commands were run from the repository root with the pinned environment in `.venv`. Values are measured outputs, not estimates.

| Measurement | Result | Method |
|---|---:|---|
| Model training | 31.4 s observed command duration | `.venv\Scripts\python scripts\train.py` |
| Training duration recorded inside script | 4.797 s | `artifacts/model_metadata.json`; starts after Python and heavy library imports |
| Unit + integration + behavioural tests with branch coverage | 5.92 s reported by pytest; 7.223 s wall time | `pytest --cov --cov-branch --cov-report=term-missing -q` |
| Full fast gate | 38.447 s | `pip check` + Ruff + strict mypy + import-linter + current/history secret scan + coverage tests |
| Branch coverage on configured core layers | 98.26% | pytest-cov; threshold is 80% |
| Tests | 38 passed | Final measured coverage run |
| Packaged model size | 279,524 bytes | `Get-Item artifacts/model.joblib` |
| Dataset snapshot size | 17,171,976 bytes | `Get-Item data/snapshot/cars.csv` |
| Docker image build time | 141.793 s | No-cache multi-stage build with Docker Engine 29.8.0 on the same host |
| Docker image size | 471,318,528 bytes (449.5 MiB) | `docker image inspect capstoneproject-api`; below the 500 MB requirement |
| Compose startup/smoke time | 31.108 s | Forced recreate with `docker compose up --detach --force-recreate --wait`, followed by real readiness and prediction requests |
| Graceful API shutdown | 1.027 s | `docker compose stop --timeout 15 api`; logs showed application shutdown complete |

Docker verification also covered non-root UID 10001, in-image model warm-up, Redis outage behavior, recovery, and absence of training-only pandas/matplotlib packages.
