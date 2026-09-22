PYTHON ?= python
IMAGE ?= used-car-assessor:local

.PHONY: install test lint image smoke

install:
	$(PYTHON) -m pip install -e ".[dev,train]"

test:
	$(PYTHON) -m pytest --cov --cov-branch --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m mypy src
	lint-imports

image:
	docker build --tag $(IMAGE) .

smoke:
	docker compose up --build --detach --wait
	curl --fail --silent http://localhost:8000/ready
	docker compose down

