.PHONY: help install install-dev format lint test security clean setup-dev run build deploy ai-assist docker-dev
.DEFAULT_GOAL := help

# Colors for output
BOLD := \033[1m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# Default target
help:
	@echo "$(BOLD)🚀 ChatterFix CMMS Development Commands$(RESET)"
	@echo ""
	@echo "$(BLUE)Setup:$(RESET)"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  setup-dev    Complete development setup"
	@echo "  quick-start  Full setup and start for new developers"
	@echo ""
	@echo "$(BLUE)Code Quality:$(RESET)"
	@echo "  format       Format code with black and isort"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  test         Run tests with coverage"
	@echo "  security     Run security checks (bandit, safety)"
	@echo "  check-all    Run all quality checks"
	@echo ""
	@echo "$(BLUE)Development:$(RESET)"
	@echo "  run          Start development server"
	@echo "  docker-dev   Start with Docker Compose"
	@echo "  build        Build Docker image"
	@echo "  deploy       Deploy to cloud"
	@echo "  clean        Clean cache and temp files"
	@echo ""
	@echo "$(BLUE)AI Assistance:$(RESET)"
	@echo "  ai-review    AI-powered code review"
	@echo "  ai-security  AI security analysis"
	@echo "  ai-optimize  AI optimization suggestions"
	@echo ""
	@echo "$(YELLOW)🎯 Built for technicians - hands-free operation first!$(RESET)"

# Installation
install:
	@echo "$(GREEN)Installing ChatterFix dependencies...$(RESET)"
	pip install -r requirements-full.txt
	@echo "$(GREEN)✅ Dependencies installed$(RESET)"

install-dev:
	pip install -r requirements-full.txt
	pip install pytest black flake8 safety bandit mypy

setup-dev: install-dev
	@echo "$(GREEN)Setting up ChatterFix development environment...$(RESET)"
	cp .env.template .env || echo "$(YELLOW).env.template not found$(RESET)"
	@echo "$(GREEN)✅ Development environment setup complete!$(RESET)"
	@echo "$(YELLOW)📝 Fill in .env with your actual values$(RESET)"

# Docker operations
build:
	@echo "$(GREEN)Building ChatterFix Docker image...$(RESET)"
	docker build -t chatterfix:latest .
	@echo "$(GREEN)✅ Docker image built$(RESET)"

docker-dev:
	@echo "$(GREEN)Starting ChatterFix with Docker Compose...$(RESET)"
	docker-compose up --build

deploy:
	@echo "$(GREEN)Deploying ChatterFix to cloud...$(RESET)"
	./scripts/deploy.sh cloud-run
	@echo "$(GREEN)✅ Deployment complete$(RESET)"

# AI assistance
ai-review:
	@echo "$(GREEN)Running AI code review...$(RESET)"
	python scripts/ai-assistant.py review --file main.py

ai-security:
	@echo "$(GREEN)Running AI security analysis...$(RESET)"
	python scripts/ai-assistant.py security

ai-optimize:
	@echo "$(GREEN)Getting AI optimization suggestions...$(RESET)"
	python scripts/ai-assistant.py optimize --file app/

# Verify all integrations
verify:
	@echo "$(GREEN)Verifying ChatterFix CMMS setup...$(RESET)"
	./scripts/verify-setup.sh

# Quick start for new developers
quick-start: setup-dev build verify
	@echo "$(GREEN)🚀 ChatterFix CMMS is ready!$(RESET)"
	@echo "$(YELLOW)🎤 Voice commands enabled$(RESET)"
	@echo "$(YELLOW)📷 OCR scanning ready$(RESET)"
	@echo "$(YELLOW)🔧 Technician workflow optimized$(RESET)"

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