.PHONY: check lint types test run migrate seed
PY ?= python3

check: lint types test

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

types:
	$(PY) -m mypy app

test:
	$(PY) -m pytest --cov=app --cov-report=term-missing

run:
	$(PY) -m uvicorn app.main:app --reload --port 8000

migrate:
	$(PY) -m alembic upgrade head

seed:
	$(PY) -m seed.load
