FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /build
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir --prefix=/install .

FROM python:3.11.9-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UCA_ENVIRONMENT=production \
    UCA_MODEL_PATH=/app/artifacts/model.joblib \
    UCA_MODEL_METADATA_PATH=/app/artifacts/model_metadata.json \
    UCA_REDIS_URL=redis://redis:6379/0

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=app:app artifacts ./artifacts
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2)"]
CMD ["uvicorn", "used_car_assessor.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

