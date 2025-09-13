.PHONY: test test-verbose install-test-deps compile-dev-deps clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  install-test-deps - Install test dependencies"
	@echo "  compile-dev-deps  - Compile development requirements"
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

# Clean up test artifacts
clean:
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete