# Benchmarks

Measured on 2026-09-21 on Windows 10 build 19045 (x64), Python 3.11.9, an Intel64 Family 6 Model 142 processor (8 logical processors), and 7.6 GB RAM. Commands were run from the repository root with the pinned environment in `.venv`. Values are measured outputs, not estimates.

| Measurement | Result | Method |
|---|---:|---|
| Model training | 31.4 s observed command duration | `.venv\Scripts\python scripts\train.py` |
| Training duration recorded inside script | 4.797 s | `artifacts/model_metadata.json`; starts after Python and heavy library imports |
| Unit + integration + behavioural tests with branch coverage | 12.50 s reported by pytest | `pytest --cov --cov-branch --cov-report=term-missing -q` inside the measured gate |
| Full fast gate | 25.553 s | Ruff + strict mypy + import-linter + current/history secret scan + coverage tests |
| Branch coverage on configured core layers | 97.55% | pytest-cov; threshold is 80% |
| Tests | 37 passed | Final measured coverage run |
| Packaged model size | 279,524 bytes | `Get-Item artifacts/model.joblib` |
| Dataset snapshot size | 17,171,976 bytes | `Get-Item data/snapshot/cars.csv` |
| Docker image build time | BLOCKED | Docker is not installed or not on `PATH` in this environment |
| Docker image size | BLOCKED | Must be measured with `docker image inspect` after Docker is available; no estimate is substituted |
| Compose startup/smoke time | BLOCKED | Docker/Compose unavailable locally; CI workflow contains the required real smoke stage but has not run remotely |

The final test count and fast-gate measurements should be refreshed after any material code/test change. Docker measurements must be added only from an actual successful build.
