.PHONY: quality format format-check lint test

quality: lint

format:
	.venv/bin/python -m ruff format app tests
	.venv/bin/python -m ruff check --fix app tests

format-check:
	.venv/bin/python -m ruff format --check app tests

lint:
	.venv/bin/python -m ruff check app tests

test:
	.venv/bin/python -m pytest
