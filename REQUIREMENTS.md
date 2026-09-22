# Capstone Requirements Traceability

Status values: `NOT_STARTED`, `IN_PROGRESS`, `VERIFIED`, `BLOCKED`.

This checklist maps the authoritative requirements in `SDA-AIE-113-Capstone_Project-v2.pdf` and the supplied implementation brief to planned implementation locations and verification evidence. A requirement becomes `VERIFIED` only after its stated check has actually run successfully.

## Current Gate and Environment

| Item | Status | Evidence / exact next action |
|---|---|---|
| Instructor approval for Track B idea | VERIFIED | Project owner supplied explicit approval confirmation on 2026-09-21; recorded in `APPROVAL_PROPOSAL.md`. Preserve the original instructor message/email separately if formal evidence is required. |
| Existing project or dataset | NOT_STARTED | Workspace inspection found only the capstone PDF; no source repository or dataset exists. |
| Local Git repository | BLOCKED | `git rev-parse --is-inside-work-tree` reported that this directory is not a Git repository. Initialize only after project approval. |
| Python | VERIFIED | `python --version` returned Python 3.11.9. |
| Docker and Compose | BLOCKED | `docker` is not installed or not on `PATH`. Install Docker Desktop with Compose, start it, and verify `docker info` plus `docker compose version`. |
| GitHub access/authentication | BLOCKED | Repository supplied as `https://github.com/nawaf-ds/car-resale-ai-service`, but anonymous `git ls-remote` returned `Repository not found`. The credential pasted into chat must be revoked and will not be used. Authenticate securely through Git Credential Manager/GitHub CLI, or correct repository visibility/URL, then retry. |
| Branch-protection administration | BLOCKED | No GitHub repository or authenticated access is available. Repository owner/admin access is required to configure rulesets or branch protection. |
| Independent approving reviewer | BLOCKED | No reviewer availability is documented. Identify at least one reviewer who can approve a pull request to `main`. |
| GNU Make | BLOCKED | `make` is not installed or not on `PATH`; required Makefile targets can be authored later but cannot yet be locally invoked. |
| `uv` package manager | NOT_STARTED | `uv` is unavailable. It is optional; standard Python tooling may be used unless the approved implementation chooses otherwise. |

## 1. Project Choice and Data

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Track B idea approved before building | VERIFIED | `APPROVAL_PROPOSAL.md` | Project owner supplied explicit instructor-approval confirmation on 2026-09-21 |
| Clear 2-3 option decision | NOT_STARTED | `src/used_car_assessor/domain/` | Policy unit tests for `BELOW_RANGE`, `WITHIN_RANGE`, `ABOVE_RANGE` |
| Tabular or short-text input only | NOT_STARTED | API schemas and dataset documentation | Schema and dataset audit |
| Lightweight model | NOT_STARTED | `src/used_car_assessor/adapters/model/` | Training script and measured CPU training run |
| Deterministic behavioural test | NOT_STARTED | `tests/behavioral/` | Real-model behavioural test run |
| Public used-car dataset with permitted usage and provenance | NOT_STARTED | `data/README.md`, model card, `README.md` | Source URL, licence/terms, and downloaded-file checksum |
| Verify availability, columns, currency, mileage units, period, and market | NOT_STARTED | `data/README.md` | Recorded source inspection and schema/data checks |
| Do not invent data, metrics, provenance, or downloads | NOT_STARTED | Repository-wide | Review against actual artifacts and command output |
| Document advertised-price versus sale-price limitation | NOT_STARTED | `README.md`, model card | Documentation review |
| Baseline plus two suitable regression models if feasible | NOT_STARTED | `scripts/train.py`, analysis report | Reproducible comparison on validation data |
| Reproducible missing-value and categorical preprocessing | NOT_STARTED | Model pipeline adapter | Unit/integration tests and serialized pipeline inspection |
| Fit learned preprocessing only on training data | NOT_STARTED | Training pipeline | Split-before-fit code review and tests |
| Prevent target and duplicate leakage | NOT_STARTED | Training pipeline | Feature audit and duplicate/group split checks |
| Asking price excluded from value-estimation features | NOT_STARTED | Feature schema and training pipeline | Feature-name assertion in tests and model metadata |
| Untouched final test set | NOT_STARTED | Training pipeline and metadata | Split manifest/checksums and one-time final evaluation |
| Report actual MAE, RMSE, and R-squared | NOT_STARTED | Model report/model metadata | Reproduced metrics from untouched test set |
| Consistent vehicle year/age handling | NOT_STARTED | Feature engineering and model card | Tests tied to dataset observation period |
| Save preprocessing, model, and metadata together | NOT_STARTED | Versioned model artifact | Startup/load integration test and metadata validation |
| Keep training tools out of runtime image where possible | NOT_STARTED | Dependency files and `Dockerfile` | Runtime dependency/image inspection |
| Concise analysis and useful charts | NOT_STARTED | `reports/` | Reproducible report generated from selected data |

## 2. Clean Architecture and Repository Layout

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Python `src` layout | NOT_STARTED | `src/used_car_assessor/` | Package/import test |
| Separate domain, service, adapters, and API layers | NOT_STARTED | Corresponding package directories | Import-linter contract passes |
| Pure domain without framework/infrastructure dependencies | NOT_STARTED | `src/used_car_assessor/domain/` | Import-linter and dependency review |
| Model behind a `Protocol` with dependency injection | NOT_STARTED | Service port plus adapter implementation | Unit test using a fake model and integration test using real adapter |
| Architectural contract automatically enforced | NOT_STARTED | `.importlinter` | `lint-imports` passes |
| Makefile targets: install, test, lint, image, smoke | NOT_STARTED | `Makefile` | Each target invoked successfully |

## 3. Service Interface and Lifecycle

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| `POST /v1/predict` | NOT_STARTED | API routes | Integration and smoke tests |
| Unified success/error envelope with trace ID | NOT_STARTED | API response/error handling | Valid and invalid request tests |
| Strict validation and unknown-field rejection | NOT_STARTED | API request schemas | Boundary and extra-field tests |
| Reject invalid numerics and unsupported categories explicitly | NOT_STARTED | API/domain validation | NaN/infinity/range/category tests |
| Model load and warm-up only during startup | NOT_STARTED | API lifespan/bootstrap | Import-side-effect and startup tests |
| Separate `GET /health` liveness | NOT_STARTED | API routes | Endpoint test independent of readiness |
| `GET /ready` reflects model and essential service availability | NOT_STARTED | API routes/readiness state | Startup and dependency-failure tests |
| Safe, consistent errors without internal detail leakage | NOT_STARTED | API exception handling | Error-response and log tests |
| Graceful shutdown and resource closure | NOT_STARTED | API lifespan and adapters | Process/container stop verification |

## 4. Containerisation and Compose

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Multi-stage image no larger than 500 MB | BLOCKED | `Dockerfile` | Build and measured `docker image inspect`; Docker unavailable locally |
| Non-root runtime user | NOT_STARTED | `Dockerfile` | Container identity check |
| Healthcheck targets `/ready` | NOT_STARTED | `Dockerfile` | Image inspection and unhealthy-model test |
| Clean shutdown on stop | BLOCKED | Runtime/lifespan | Timed `docker stop` logs; Docker unavailable locally |
| Compose includes one genuinely useful supporting service | NOT_STARTED | `docker-compose.yml`, decision record | Functional dependency integration and failure test |
| Startup gated on real health | NOT_STARTED | `docker-compose.yml` | Compose startup/failure observation |
| Pinned dependencies and image versions; no production `:latest` | NOT_STARTED | Lock files, Docker/Compose, workflow | Repository search and build inspection |
| Measure actual image size | BLOCKED | `BENCHMARKS.md` | Docker image measurement after Docker is available |

## 5. Tests and Quality Gates

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Meaningful unit tests | NOT_STARTED | `tests/unit/` | Test run |
| Integration tests | NOT_STARTED | `tests/integration/` | Test run |
| Behavioural tests against the real model | NOT_STARTED | `tests/behavioral/` | Test run using selected artifact |
| Invariance to irrelevant identifier | NOT_STARTED | Behavioural tests | Same prediction/decision under identifier change |
| Directional asking-price behaviour | NOT_STARTED | Behavioural tests | Increasing asking price never moves toward a cheaper band |
| Versioned golden reference with provenance and tolerances | NOT_STARTED | `tests/behavioral/golden/` | Reviewed fixture and golden test |
| Never regenerate golden merely to pass | NOT_STARTED | Contributor docs / golden provenance | Review process documented |
| Avoid unsupported model monotonicity assertions | NOT_STARTED | Behavioural tests | Test review confirms policy-only directional claim |
| At least 80% branch coverage on identified core layers | NOT_STARTED | Coverage configuration | Coverage report and enforced threshold |
| Fast quality gate at most 60 seconds | NOT_STARTED | Makefile/script and `BENCHMARKS.md` | Timed local run |
| Invalid request and decision-boundary tests | NOT_STARTED | Unit/integration tests | Test run |
| Startup/readiness and supporting-service failure tests | NOT_STARTED | Integration tests | Test run |
| Lint, type-check, import-linter, and tests pass | NOT_STARTED | Tool configuration | Fast/full quality-gate output |

## 6. CI/CD and GitHub

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Ordered stages: lint/type-check, tests/coverage, image smoke, publish | NOT_STARTED | `.github/workflows/ci.yml` | Actual GitHub Actions run graph |
| Architectural checks and secret scanning | NOT_STARTED | CI workflow | Actual check output |
| Checks run for pull requests | NOT_STARTED | CI workflow | Pull-request run |
| Publish only after merged PR reaches `main` | NOT_STARTED | CI workflow | Trigger/condition review and actual main run |
| GHCR tag is full commit SHA, never `latest` | NOT_STARTED | CI workflow | Published package tag inspection |
| Least-privilege permissions and GitHub authentication | NOT_STARTED | CI workflow | Workflow review |
| Main protection: required checks, one review, no force-push | BLOCKED | GitHub repository settings | API/UI evidence after repository and admin access exist |
| Actual passing run on `main` | BLOCKED | GitHub Actions | Run URL; repository/access unavailable |
| Actual published GHCR image | BLOCKED | GHCR | Package URL and SHA tag; repository/access unavailable |

## 7. Configuration, Secrets, and Logging

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Central typed settings with immediate validation | NOT_STARTED | Configuration module | Valid/invalid configuration tests |
| Safe placeholder-only `.env.example` | NOT_STARTED | `.env.example` | Manual and secret-scan review |
| Structured JSON logs correlated by trace ID | NOT_STARTED | Logging middleware/config | Captured log tests |
| No sensitive data, credentials, or full request bodies in logs | NOT_STARTED | Logging implementation | Captured log tests and review |
| Scan current files and Git history for secrets | BLOCKED | CI and local command | Current tree can be scanned later; no Git history exists yet |

## 8. Deliverables

| Requirement | Status | Planned location | Verification evidence |
|---|---|---|---|
| Working GitHub repository URL | BLOCKED | `https://github.com/nawaf-ds/car-resale-ai-service` | Anonymous access returned `Repository not found`; secure authenticated access or corrected visibility/URL is required |
| Five or more genuine incremental commits | BLOCKED | Git history | `git log`; no repository exists and implementation is approval-gated |
| Passing CI on `main` with published GHCR image | BLOCKED | GitHub Actions/GHCR | Run and package URLs |
| New-engineer runbook usable within 10 minutes | NOT_STARTED | `README.md` | Fresh-environment walkthrough |
| Real benchmark measurements and environment/method | BLOCKED | `BENCHMARKS.md` | Measured builds/tests/image; required tooling incomplete |
| Five substantive decisions with rationale | NOT_STARTED | `DECISIONS.md` | Documentation review |
| One useful implemented and tested extension | NOT_STARTED | To be selected after approval | Feature-specific tests |
| Five-minute demo guide | NOT_STARTED | `DEMO.md` | Timed rehearsal |
| Presenter explanation of model, policy, limitations, choices | NOT_STARTED | `README.md`, model card, `DEMO.md` | Documentation review and rehearsal |

## 9. Final Audit Rules

| Rule | Status | Evidence / control |
|---|---|---|
| Never claim an unrun command passed | IN_PROGRESS | Verification evidence must cite actual command output |
| Distinguish local, Docker, and remote verification | IN_PROGRESS | Status reports and final audit use separate evidence labels |
| Do not fabricate measurements, provenance, CI, or permissions | IN_PROGRESS | Block missing evidence instead of estimating |
| Do not weaken checks or hide failures | IN_PROGRESS | Failures remain documented until resolved |
| Keep documentation synchronized | NOT_STARTED | Final repository audit |
| No arbitrary golden regeneration | NOT_STARTED | Golden provenance/review workflow |
| No production `:latest` tag | NOT_STARTED | Repository search and published-tag inspection |
| No meaningless coverage inflation | NOT_STARTED | Core-layer scope and test review |
| Original work with no unexplained peer similarity | NOT_STARTED | Implementation and commit history review |
