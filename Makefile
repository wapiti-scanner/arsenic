# Makefile for the arsenic project

.PHONY: all test release format lint docs clean

# Default target when running `make`
all: format lint test

# Run tests
test:
	@echo "--- Running tests ---"
	poetry run pytest

# Create sdist and wheel distributions
release:
	@echo "--- Building release artifacts ---"
	poetry build

# Format code using black
format:
	@echo "--- Formatting code ---"
	poetry run black src tests docs

# Lint code using pylint
lint:
	@echo "--- Linting code ---"
	poetry run pylint src tests

# Generate documentation
docs:
	@echo "--- Generating documentation ---"
	$(MAKE) -C docs html

# Clean up generated files
clean:
	@echo "--- Cleaning up project ---"
	rm -rf dist
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	$(MAKE) -C docs clean
