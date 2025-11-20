.PHONY: install test lint format clean run run-dev help

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install project dependencies
	uv pip install -e ".[dev]"

test:  ## Run tests with coverage
	pytest tests/ -v --cov=src/daily_ai_insight --cov-report=html --cov-report=term

test-unit:  ## Run only unit tests
	pytest tests/unit/ -v

test-integration:  ## Run only integration tests
	pytest tests/integration/ -v

lint:  ## Run linters
	ruff check src/ tests/
	mypy src/

format:  ## Format code
	black src/ tests/
	ruff check --fix src/ tests/

clean:  ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	rm -rf dist build *.egg-info

run:  ## Run the pipeline
	python -m daily_ai_insight

run-dev:  ## Run in development mode (skip analysis)
	python -m daily_ai_insight --skip-analysis

run-cleanup:  ## Clean up old storage files
	python -m daily_ai_insight --cleanup

uv-sync:  ## Sync dependencies with uv
	uv pip compile pyproject.toml -o requirements.txt
	uv pip install -r requirements.txt