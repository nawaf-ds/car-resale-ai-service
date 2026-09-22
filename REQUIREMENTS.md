# Capstone Requirements Traceability

Status values: `NOT_STARTED`, `IN_PROGRESS`, `VERIFIED`, `BLOCKED`.

This checklist maps the authoritative requirements in `SDA-AIE-113-Capstone_Project-v2.pdf` and the supplied implementation brief to planned implementation locations and verification evidence. A requirement becomes `VERIFIED` only after its stated check has actually run successfully.

## Current Gate and Environment

| Item | Status | Evidence / exact next action |
|---|---|---|
| Instructor approval for Track B idea | VERIFIED | Project owner supplied explicit approval confirmation on 2026-09-21; recorded in `APPROVAL_PROPOSAL.md`. Preserve the original instructor message/email separately if formal evidence is required. |
| Existing project or dataset | VERIFIED | Approved project and checksum-pinned dataset snapshot now exist locally. |
| Local Git repository | VERIFIED | Local `main` repository initialized with five genuine staged commits. |
| Python | VERIFIED | `python --version` returned Python 3.11.9. |
| Docker and Compose | BLOCKED | `docker` is not installed or not on `PATH`. Install Docker Desktop with Compose, start it, and verify `docker info` plus `docker compose version`. |
| GitHub access/authentication | BLOCKED | Repository supplied as `https://github.com/nawaf-ds/car-resale-ai-service`, but anonymous `git ls-remote` returned `Repository not found`. The credential pasted into chat must be revoked and will not be used. Authenticate securely through Git Credential Manager/GitHub CLI, or correct repository visibility/URL, then retry. |
| Branch-protection administration | BLOCKED | No GitHub repository or authenticated access is available. Repository owner/admin access is required to configure rulesets or branch protection. |
| Independent approving reviewer | BLOCKED | No reviewer availability is documented. Identify at least one reviewer who can approve a pull request to `main`. |
| GNU Make | BLOCKED | `make` is not installed or not on `PATH`; required Makefile targets can be authored later but cannot yet be locally invoked. |
| `uv` package manager | VERIFIED | Optional and not selected; standard Python/pip tooling is documented and verified. |

## 1. Project Choice and Data

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Track B idea approved before building | VERIFIED | `APPROVAL_PROPOSAL.md` | Project owner supplied explicit instructor-approval confirmation on 2026-09-21 |
| Clear 2-3 option decision | VERIFIED | `src/used_car_assessor/domain/` | Boundary tests cover all three bands |
| Tabular or short-text input only | VERIFIED | API schemas and `data/README.md` | Five tabular model features audited |
| Lightweight model | VERIFIED | `src/used_car_assessor/adapters/model.py` | CPU training completed; artifact is 279,524 bytes |
| Deterministic behavioural test | VERIFIED | `tests/behavioral/` | 3 real-model behavioural tests passed |
| Public used-car dataset with permitted usage and provenance | VERIFIED | `data/README.md`, `README.md` | Official Kaggle metadata, Apache 2.0, source links, hashes recorded |
| Verify availability, columns, currency, mileage units, period, and market | VERIFIED | `data/README.md` | Actual 144,867x7 snapshot audited; missing exact scrape window disclosed |
| Do not invent data, metrics, provenance, or downloads | VERIFIED | Repository-wide | Reports and docs use generated artifacts and observed output |
| Document advertised-price versus sale-price limitation | VERIFIED | `README.md`, `data/README.md` | Limitation stated explicitly |
| Baseline plus two suitable regression models if feasible | VERIFIED | `scripts/train.py`, `reports/model_evaluation.json` | Median, Ridge, and histogram-gradient validation metrics recorded |
| Reproducible missing-value and categorical preprocessing | VERIFIED | Serialized sklearn pipelines | Imputation/encoding are pipeline steps |
| Fit learned preprocessing only on training data | VERIFIED | `scripts/train.py` | Split occurs before candidate pipeline fit |
| Prevent target and duplicate leakage | VERIFIED | `scripts/train.py` | Asking price excluded; exact duplicates dropped before split |
| Asking price excluded from value-estimation features | VERIFIED | Feature schema and metadata | Five feature names recorded; metadata asserts false |
| Untouched final test set | VERIFIED | Training pipeline and metadata | 8,315-row test set evaluated only after validation selection/refit |
| Report actual MAE, RMSE, and R-squared | VERIFIED | `reports/model_evaluation.json` | Test MAE 6317.40, RMSE 10895.72, R2 0.8223 |
| Consistent vehicle year/age handling | VERIFIED | API schema/training | Raw model year used consistently; accepted range is dataset-supported 1990-2024 |
| Save preprocessing, model, and metadata together | VERIFIED | `artifacts/` | Checksum-validated load and warm-up test passed |
| Keep training tools out of runtime image where possible | IN_PROGRESS | Dependency extras and `Dockerfile` | Training extras excluded from runtime install; image inspection blocked by missing Docker |
| Concise analysis and useful charts | VERIFIED | `reports/` | Metrics JSON and two visually inspected charts generated |

## 2. Clean Architecture and Repository Layout

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Python `src` layout | VERIFIED | `src/used_car_assessor/` | Package installed editable and tests imported it |
| Separate domain, service, adapters, and API layers | VERIFIED | Corresponding package directories | Import-linter layer contract kept |
| Pure domain without framework/infrastructure dependencies | VERIFIED | `src/used_car_assessor/domain/` | Forbidden-import contract kept |
| Model behind a `Protocol` with dependency injection | VERIFIED | `service/ports.py` plus adapters | Fake and real implementations exercised |
| Architectural contract automatically enforced | VERIFIED | `.importlinter` | 2 contracts kept, 0 broken |
| Makefile targets: install, test, lint, image, smoke | IN_PROGRESS | `Makefile` | Targets authored; GNU Make and Docker unavailable locally |

## 3. Service Interface and Lifecycle

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| `POST /v1/predict` | VERIFIED | API routes | Fake and real-model integration/behaviour tests passed |
| Unified success/error envelope with trace ID | VERIFIED | API response/error handling | Success, validation, readiness, and internal-error tests passed |
| Strict validation and unknown-field rejection | VERIFIED | API request schemas | Strict types, ranges, and extra-field test passed |
| Reject invalid numerics and unsupported categories explicitly | VERIFIED | API/domain validation | Numeric-string/non-finite schema controls and unsupported-category test |
| Model load and warm-up only during startup | VERIFIED | API lifespan/bootstrap | Real behavioural client starts/warm-ups model in lifespan |
| Separate `GET /health` liveness | VERIFIED | API routes | Remains 200 during dependency failure test |
| `GET /ready` reflects model and essential service availability | VERIFIED | API routes/readiness state | Model and supporting-service failure tests return 503 |
| Safe, consistent errors without internal detail leakage | VERIFIED | API exception handling | Internal exception detail is absent from 500 response |
| Graceful shutdown and resource closure | IN_PROGRESS | API lifespan and adapters | Recorder close verified in integration test; container stop blocked by Docker |

## 4. Containerisation and Compose

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Multi-stage image no larger than 500 MB | BLOCKED | `Dockerfile` | Build and measured `docker image inspect`; Docker unavailable locally |
| Non-root runtime user | IN_PROGRESS | `Dockerfile` | UID 10001 configured; runtime identity check blocked by Docker |
| Healthcheck targets `/ready` | IN_PROGRESS | `Dockerfile` | Definition reviewed; image execution blocked by Docker |
| Clean shutdown on stop | BLOCKED | Runtime/lifespan | Timed `docker stop` logs; Docker unavailable locally |
| Compose includes one genuinely useful supporting service | VERIFIED | `docker-compose.yml`, `DECISIONS.md` | Redis-backed `/v1/stats` extension and dependency-failure test |
| Startup gated on real health | IN_PROGRESS | `docker-compose.yml` | Health condition configured; execution blocked by Docker |
| Pinned dependencies and image versions; no production `:latest` | VERIFIED | Pyproject, Docker/Compose, workflow | Exact Python dependencies and image/action versions; repository search shows no production latest tag |
| Measure actual image size | BLOCKED | `BENCHMARKS.md` | Docker image measurement after Docker is available |

## 5. Tests and Quality Gates

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Meaningful unit tests | VERIFIED | `tests/unit/` | Full local test run passed |
| Integration tests | VERIFIED | `tests/integration/` | Full local test run passed |
| Behavioural tests against the real model | VERIFIED | `tests/behavioral/` | 3 behavioural tests passed |
| Invariance to irrelevant identifier | VERIFIED | Behavioural tests | `listing_id` A/B produced identical response data |
| Directional asking-price behaviour | VERIFIED | Behavioural tests | Band order observed 0,1,2 with fixed estimate |
| Versioned golden reference with provenance and tolerances | VERIFIED | `tests/behavioral/golden/` | v1 fixture passed with hashes and $0.05 tolerance |
| Never regenerate golden merely to pass | VERIFIED | Golden governance README | Review/change rule documented |
| Avoid unsupported model monotonicity assertions | VERIFIED | Behavioural tests | Directionality asserted only over asking-price policy |
| At least 80% branch coverage on identified core layers | VERIFIED | Coverage configuration | 97.55% measured on final local gate |
| Fast quality gate at most 60 seconds | VERIFIED | Makefile and `BENCHMARKS.md` | Full gate measured at 25.553 seconds |
| Invalid request and decision-boundary tests | VERIFIED | Unit/integration tests | Boundary and malformed request tests passed |
| Startup/readiness and supporting-service failure tests | VERIFIED | Integration tests | Model and recorder failure paths passed |
| Lint, type-check, import-linter, and tests pass | VERIFIED | Tool configuration | Combined local gate passed |

## 6. CI/CD and GitHub

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Ordered stages: lint/type-check, tests/coverage, image smoke, publish | IN_PROGRESS | `.github/workflows/ci.yml` | Dependency chain authored and YAML parsed; remote run unavailable |
| Architectural checks and secret scanning | IN_PROGRESS | CI workflow | Configured; local equivalents pass, remote output unavailable |
| Checks run for pull requests | IN_PROGRESS | CI workflow | Trigger authored; pull-request run unavailable |
| Publish only after merged PR reaches `main` | IN_PROGRESS | CI workflow | Push-main condition relies on required PR branch protection, which remains blocked |
| GHCR tag is full commit SHA, never `latest` | IN_PROGRESS | CI workflow | Full `${{ github.sha }}` tag configured; no published image yet |
| Least-privilege permissions and GitHub authentication | VERIFIED | CI workflow | Default read-only plus package write only in publish; `GITHUB_TOKEN` used |
| Main protection: required checks, one review, no force-push | BLOCKED | GitHub repository settings | API/UI evidence after repository and admin access exist |
| Actual passing run on `main` | BLOCKED | GitHub Actions | Run URL; repository/access unavailable |
| Actual published GHCR image | BLOCKED | GHCR | Package URL and SHA tag; repository/access unavailable |

## 7. Configuration, Secrets, and Logging

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Central typed settings with immediate validation | VERIFIED | `api/settings.py` | Invalid values raise typed validation errors |
| Safe placeholder-only `.env.example` | VERIFIED | `.env.example` | Manual review and secret scan passed |
| Structured JSON logs correlated by trace ID | VERIFIED | Logging middleware/config | JSON request logs observed during integration tests |
| No sensitive data, credentials, or full request bodies in logs | VERIFIED | Logging implementation | Middleware logs metadata only; safe 500 response test passed |
| Scan current files and Git history for secrets | VERIFIED | `scripts/check_secrets.py` | Actual result: 0 current-tree findings, 0 history findings |

## 8. Deliverables

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Working GitHub repository URL | BLOCKED | `https://github.com/nawaf-ds/car-resale-ai-service` | Anonymous access returned `Repository not found`; secure authenticated access or corrected visibility/URL is required |
| Five or more genuine incremental commits | VERIFIED | Local Git history | Five staged commits shown by `git log --oneline -5` |
| Passing CI on `main` with published GHCR image | BLOCKED | GitHub Actions/GHCR | Run and package URLs |
| New-engineer runbook usable within 10 minutes | IN_PROGRESS | `README.md` | Runbook authored; clean Docker walkthrough blocked by missing Docker |
| Real benchmark measurements and environment/method | IN_PROGRESS | `BENCHMARKS.md` | Local measurements recorded; image size/build/smoke remain blocked |
| Five substantive decisions with rationale | VERIFIED | `DECISIONS.md` | Six decisions documented |
| One useful implemented and tested extension | VERIFIED | `/v1/stats`, Redis adapter | Extension integration test passed |
| Five-minute demo guide | IN_PROGRESS | `DEMO.md` | Script authored; Compose rehearsal blocked by missing Docker |
| Presenter explanation of model, policy, limitations, choices | VERIFIED | `README.md`, `DECISIONS.md`, `DEMO.md` | Concise explanation documented |

## 9. Final Audit Rules

| Rule | Status | Evidence / control |
|---|---|---|
| Never claim an unrun command passed | VERIFIED | Verification evidence cites actual command output |
| Distinguish local, Docker, and remote verification | VERIFIED | Matrix and benchmarks label blocked Docker/remote evidence |
| Do not fabricate measurements, provenance, CI, or permissions | VERIFIED | Missing evidence remains blocked instead of estimated |
| Do not weaken checks or hide failures | VERIFIED | Coverage, readiness, secret, and remote blockers remain visible |
| Keep documentation synchronized | VERIFIED | Final local gate and metrics synchronized on 2026-09-21 |
| No arbitrary golden regeneration | VERIFIED | Golden provenance/review workflow documented |
| No production `:latest` tag | VERIFIED | Repository configuration reviewed; no production latest tag |
| No meaningless coverage inflation | VERIFIED | Core scope explicit; tests exercise domain, failures, lifecycle, and real model |
| Original work with no unexplained peer similarity | IN_PROGRESS | Implementation and commit history are original to this workspace; external institutional review remains outside local verification |
