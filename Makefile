.PHONY: test test-verbose install-test-deps compile-dev-deps clean lint format lint-check help run-bunkr test-bunkr

# Default target
help:
	@echo "Available targets:"
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  install-test-deps - Install test dependencies"
	@echo "  compile-dev-deps  - Compile development requirements"
	@echo "  lint              - Run ruff linting and formatting"
	@echo "  lint-check        - Check code formatting and linting without fixing"
	@echo "  format            - Format code with ruff"
	@echo "  clean             - Remove test artifacts and cache"
	@echo "  help              - Show this help message"

# Compile development requirements
compile-dev-deps:
	pip install pip-tools
	pip-compile requirements-dev.in

# Install test dependencies
install-test-deps: requirements-dev.txt
	pip install -r requirements-dev.txt

# Run tests with default settings
test:
	python -m pytest tests/ -v

# Run tests with verbose output and show local variables on failure
test-verbose:
	python -m pytest tests/ -v -s --tb=long

# Run ruff linting and formatting (fix issues)
lint:
	ruff check --fix
	ruff format

# Check code formatting and linting without fixing
lint-check:
	ruff check --no-fix
	ruff format --check

# Format code with ruff
format:
	ruff format

# Run Bunkr UI server
run-bunkr:
	uvicorn src.bunkr_ui.app:create_app --factory --host 127.0.0.1 --port 8000 --reload

# Run Bunkr UI tests only
test-bunkr:
	python -m pytest tests/bunkr_ui/ -v

# Clean up test artifacts
clean:
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
