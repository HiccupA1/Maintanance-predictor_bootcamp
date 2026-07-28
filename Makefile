# Developer workflow targets for the Work Order Management backend.
# All commands are non-interactive and CI-friendly.

.PHONY: install run test lint format format-check migrate migrate-create

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest

lint:
	ruff check app tests

format:
	black app tests

format-check:
	black --check app tests

migrate:
	alembic upgrade head

# Usage: make migrate-create m="add new column"
migrate-create:
	alembic revision --autogenerate -m "$(m)"
