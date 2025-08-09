.PHONY: format lint type-check check dev

format:
	black .
	ruff check --fix .

lint:
	ruff check .
	black --check .

type-check:
	mypy .

check: lint type-check

dev:
	uvicorn main:app --host 0.0.0.0 --port 8000