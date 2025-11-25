# =============================================================================
# Obscura V2 - Makefile
# =============================================================================
# Convenient commands for development and deployment
# =============================================================================

.PHONY: help install dev test lint format clean docker-up docker-down \
        docker-build migrate logs shell db-shell redis-shell

# Default target
help:
	@echo "Obscura V2 - Modular Monolith Backend"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  install       Install Python dependencies"
	@echo "  dev           Start development server (API Gateway)"
	@echo "  dev-trading   Start trading service standalone"
	@echo "  dev-analytics Start analytics service standalone"
	@echo "  test          Run all tests"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up     Start all services"
	@echo "  docker-down   Stop all services"
	@echo "  docker-build  Build all containers"
	@echo "  docker-logs   Follow container logs"
	@echo "  docker-full   Start full microservices mode"
	@echo ""
	@echo "Database:"
	@echo "  migrate       Run database migrations"
	@echo "  migrate-new   Create new migration"
	@echo "  db-shell      Open PostgreSQL shell"
	@echo "  redis-shell   Open Redis CLI"
	@echo ""
	@echo "Utilities:"
	@echo "  clean         Remove cache and build artifacts"
	@echo "  shell         Open Python shell with app context"
	@echo "  health        Check service health"

# =============================================================================
# Development
# =============================================================================

install:
	pip install -r requirements.txt

dev:
	cd modules/api_gateway && uvicorn gateway:app --reload --host 0.0.0.0 --port 8000

dev-trading:
	cd modules/trading && uvicorn service:app --reload --host 0.0.0.0 --port 8001

dev-subscriptions:
	cd modules/subscriptions && uvicorn service:app --reload --host 0.0.0.0 --port 8002

dev-copy-trading:
	cd modules/copy_trading && uvicorn service:app --reload --host 0.0.0.0 --port 8003

dev-analytics:
	cd modules/analytics && uvicorn service:app --reload --host 0.0.0.0 --port 8004

dev-citadel:
	cd modules/citadel && uvicorn service:app --reload --host 0.0.0.0 --port 8005

# =============================================================================
# Testing
# =============================================================================

test:
	pytest -v --tb=short

test-cov:
	pytest -v --cov=modules --cov=shared --cov-report=html --cov-report=term

test-trading:
	pytest -v modules/trading/tests/

test-analytics:
	pytest -v modules/analytics/tests/

test-copy-trading:
	pytest -v modules/copy_trading/tests/

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check modules/ shared/
	mypy modules/ shared/ --ignore-missing-imports

format:
	ruff format modules/ shared/
	isort modules/ shared/

# =============================================================================
# Docker
# =============================================================================

docker-up:
	docker-compose up -d postgres redis api-gateway

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-full:
	docker-compose --profile full up -d

docker-standalone:
	docker-compose --profile standalone up -d

docker-clean:
	docker-compose down -v --rmi local
	docker system prune -f

# =============================================================================
# Database
# =============================================================================

migrate:
	alembic upgrade head

migrate-new:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-down:
	alembic downgrade -1

migrate-history:
	alembic history

migrate-status:
	alembic current

db-shell:
	docker-compose exec postgres psql -U obscura -d obscura

redis-shell:
	docker-compose exec redis redis-cli -a $${REDIS_PASSWORD:-obscura_redis}

# =============================================================================
# Utilities
# =============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml

shell:
	python -c "from shared.database.connection import *; from shared.database.models import *; import asyncio" && python

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "API Gateway: DOWN"
	@curl -s http://localhost:8001/health | jq . 2>/dev/null || echo "Trading: DOWN"
	@curl -s http://localhost:8002/health | jq . 2>/dev/null || echo "Subscriptions: DOWN"
	@curl -s http://localhost:8003/health | jq . 2>/dev/null || echo "Copy Trading: DOWN"
	@curl -s http://localhost:8004/health | jq . 2>/dev/null || echo "Analytics: DOWN"
	@curl -s http://localhost:8005/health | jq . 2>/dev/null || echo "Citadel: DOWN"

# =============================================================================
# Production
# =============================================================================

prod-build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# =============================================================================
# Module-specific builds
# =============================================================================

build-trading:
	docker build -f modules/trading/Dockerfile -t obscura-trading .

build-subscriptions:
	docker build -f modules/subscriptions/Dockerfile -t obscura-subscriptions .

build-copy-trading:
	docker build -f modules/copy_trading/Dockerfile -t obscura-copy-trading .

build-analytics:
	docker build -f modules/analytics/Dockerfile -t obscura-analytics .

build-citadel:
	docker build -f modules/citadel/Dockerfile -t obscura-citadel .

build-gateway:
	docker build -f modules/api_gateway/Dockerfile -t obscura-api-gateway .
