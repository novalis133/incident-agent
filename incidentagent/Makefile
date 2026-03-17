.PHONY: help build up down logs api-logs dashboard-logs stop restart clean test lint format

help:
	@echo "IncidentAgent Docker Commands"
	@echo "============================="
	@echo ""
	@echo "Usage:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start services (docker-compose up)"
	@echo "  make down           - Stop services (docker-compose down)"
	@echo "  make restart        - Restart services"
	@echo "  make stop           - Stop services without removing containers"
	@echo "  make logs           - View all service logs"
	@echo "  make api-logs       - View API service logs"
	@echo "  make dashboard-logs - View Dashboard service logs"
	@echo "  make clean          - Remove containers, volumes, and images"
	@echo "  make test           - Run tests inside container"
	@echo "  make lint           - Run linting inside container"
	@echo "  make format         - Format code with black and ruff"
	@echo "  make shell-api      - Open shell in API container"
	@echo "  make shell-dashboard - Open shell in dashboard container"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  API:       http://localhost:8000"
	@echo "  Dashboard: http://localhost:8501"
	@echo "  API Docs:  http://localhost:8000/docs"

down:
	docker-compose down

stop:
	docker-compose stop

restart: down up

logs:
	docker-compose logs -f

api-logs:
	docker-compose logs -f api

dashboard-logs:
	docker-compose logs -f dashboard

clean:
	docker-compose down -v
	docker system prune -f

test:
	docker-compose exec api pytest -v --cov=incidentagent tests/

lint:
	docker-compose exec api ruff check .
	docker-compose exec api mypy incidentagent/

format:
	docker-compose exec api black incidentagent/
	docker-compose exec api ruff check --fix .

shell-api:
	docker-compose exec api /bin/bash

shell-dashboard:
	docker-compose exec dashboard /bin/bash

health:
	@echo "API Health:"
	curl -s http://localhost:8000/health | python -m json.tool
	@echo ""
	@echo "Elasticsearch Health:"
	curl -s http://localhost:9200/_cluster/health | python -m json.tool
