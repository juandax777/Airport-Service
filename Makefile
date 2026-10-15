PYTHON ?= python

.PHONY: install up down clean test lint format typecheck compose-check compose-build

install:
	$(PYTHON) -m pip install -e '.[dev]'

up:
	docker compose up --build

down:
	docker compose down

clean:
	docker compose down

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check services

format:
	$(PYTHON) -m ruff check services --fix
	$(PYTHON) -m ruff format services

typecheck:
	$(PYTHON) -m mypy services

compose-check:
	docker compose config --quiet

compose-build:
	docker compose build
