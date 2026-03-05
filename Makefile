.PHONY: help install dev lint format check-fmt clean test run build publish

# Default target
help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Install development dependencies"
	@echo "  make lint        - Run linter (ruff check)"
	@echo "  make format      - Format code with ruff"
	@echo "  make check-fmt   - Check if code is formatted"
	@echo "  make clean       - Clean up cache files"
	@echo "  make test        - Run tests"
	@echo "  make run         - Run the MCP server"
	@echo "  make build       - Build distribution packages"
	@echo "  make publish     - Publish to PyPI (requires API token)"

# Install dependencies
install:
	uv sync

# Install development dependencies
dev:
	uv sync --dev

# Run linter
lint:
	@echo "Running ruff linter..."
	uv run ruff check src/ .

# Format code
format:
	@echo "Formatting code with ruff..."
	uv run ruff format src/ .

# Check if code is formatted (fails if not)
check-fmt:
	@echo "Checking code formatting..."
	uv run ruff format --check src/ .

# Fix linting issues automatically
lint-fix:
	@echo "Fixing linting issues..."
	uv run ruff check --fix src/ .

# Clean up cache files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .venv/ 2>/dev/null || true

# Run tests
test:
	@echo "Running tests..."
	uv run pytest tests/ -v

# Run the MCP server
run:
	@echo "Starting MCP server..."
	uv run roboteditmcp

# Build distribution packages
build:
	@echo "Building distribution packages..."
	uv build

# Publish to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD)
publish:
	@echo "Publishing to PyPI..."
	uv run twine upload dist/*

# Create a git tag and push (triggers GitHub Actions publish)
tag:
	@echo "Creating and pushing git tag..."
	@read -p "Enter version (e.g., v0.1.1): " version; \
	git tag -a "$$version" -m "Release $$version"; \
	git push origin $$version
