.PHONY: lint format test dev clean

lint:
	uvx ruff check .

format:
	uvx ruff format .

test:
	uv run pytest

dev:
	uv run python main.py

clean:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
