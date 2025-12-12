.PHONY: help install install-dev format lint test security clean setup-dev run

# Default target
help:
	@echo "🚀 ChatterFix CMMS Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  setup-dev    Complete development setup (install + pre-commit)"
	@echo ""
	@echo "Code Quality:"
	@echo "  format       Format code with black and isort"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  test         Run tests with coverage"
	@echo "  security     Run security checks (bandit, safety)"
	@echo "  check-all    Run all quality checks"
	@echo ""
	@echo "Development:"
	@echo "  run          Start development server"
	@echo "  clean        Clean cache and temp files"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

setup-dev: install-dev
	pre-commit install
	@echo "✅ Development environment setup complete!"

# Code formatting
format:
	@echo "🎨 Formatting code..."
	isort app/ *.py
	black app/ *.py
	@echo "✅ Code formatting complete!"

# Linting
lint:
	@echo "🔍 Running linting..."
	flake8 app/ *.py
	mypy app/ --ignore-missing-imports
	@echo "✅ Linting complete!"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=app --cov-report=term-missing
	@echo "✅ Tests complete!"

# Security checks
security:
	@echo "🔒 Running security checks..."
	bandit -r app/ --severity-level medium
	safety check
	@echo "✅ Security checks complete!"

# Run all quality checks
check-all: format lint test security
	@echo "✅ All quality checks passed!"

# Development server
run:
	@echo "🚀 Starting ChatterFix CMMS development server..."
	python main.py

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "✅ Cleanup complete!"

# Quick development cycle
dev: format lint
	@echo "✅ Development cycle complete - ready to commit!"