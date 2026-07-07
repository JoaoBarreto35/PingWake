.PHONY: install run test lint format type-check migrate migration docker-up docker-down

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

type-check:
	mypy app

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(name)"

docker-up:
	docker compose up --build

docker-down:
	docker compose down
