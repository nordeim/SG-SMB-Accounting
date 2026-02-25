# LedgerSG Backend Makefile

.PHONY: help install dev test test-cov lint format typecheck migrate shell celery celery-beat docker-up docker-down clean

# Default target
help:
	@echo "LedgerSG Backend - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Start development server"
	@echo "  make test         - Run test suite"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Run ruff formatter"
	@echo "  make typecheck    - Run mypy"
	@echo "  make migrate      - Run Django migrations"
	@echo "  make shell        - Django shell with IPython"
	@echo "  make celery       - Start Celery worker"
	@echo "  make celery-beat  - Start Celery beat scheduler"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make clean        - Remove Python cache files"
	@echo ""

# Installation
install:
	pip install -e ".[dev]"

# Development server
dev:
	python manage.py runserver

# Testing
test:
	pytest

test-cov:
	pytest --cov=apps --cov=common --cov-report=html --cov-report=term

# Linting and formatting
lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy apps common config

# Database
migrate:
	python manage.py migrate --run-syncdb

migrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus

# Celery
celery:
	celery -A config worker -l info

celery-beat:
	celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# All checks (for CI)
check: lint format-check typecheck test
	@echo "All checks passed!"
