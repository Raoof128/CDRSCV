.PHONY: install lint test format

install:
	pip install -e .[dev]

lint:
	ruff check .
	mypy cdrcsv

format:
	ruff check . --fix

test:
	pytest -q --cov=cdrcsv --cov-report=term-missing
