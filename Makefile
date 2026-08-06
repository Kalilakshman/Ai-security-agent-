.PHONY: install test lint format clean docker-build docker-run help

.DEFAULT_GOAL := help

install: ## Install package in editable mode with development dependencies
	pip install -e .[dev]

test: ## Run unit and integration test suite with pytest
	pytest tests/ -v --cov=app --cov=core --cov=plugins --cov=memory --cov=reports

lint: ## Run ruff and mypy code quality linters
	ruff check .
	mypy app core plugins memory reports

format: ## Format code using ruff
	ruff format .

clean: ## Clean python bytecode, build, and test artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +

docker-build: ## Build multi-stage Docker image
	docker build -t security-ai-orchestrator:latest .

docker-run: ## Run Docker container CLI doctor command
	docker run --rm -it security-ai-orchestrator:latest doctor

help: ## Show Makefile targets help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
