.PHONY: help build up down logs shell migrate superuser test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-web: ## View web service logs
	docker-compose logs -f web

logs-celery: ## View Celery worker logs
	docker-compose logs -f celery

logs-db: ## View database logs
	docker-compose logs -f db

shell: ## Open shell in web container
	docker-compose exec web python manage.py shell

shell-db: ## Open shell in database
	docker-compose exec db psql -U postgres -d contract_intel

migrate: ## Run database migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker-compose exec web python manage.py makemigrations

superuser: ## Create superuser
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose exec web python manage.py collectstatic

test: ## Run tests
	docker-compose exec web python manage.py test

test-verbose: ## Run tests with verbose output
	docker-compose exec web python manage.py test -v 2

clean: ## Clean up containers, images, and volumes
	docker-compose down -v --rmi all
	docker system prune -f

restart: ## Restart all services
	docker-compose restart

restart-web: ## Restart web service
	docker-compose restart web

restart-celery: ## Restart Celery worker
	docker-compose restart celery

status: ## Show status of all services
	docker-compose ps

health: ## Check system health
	curl -f http://localhost:8000/healthz/ || echo "Health check failed"

api-docs: ## Open API documentation in browser
	open http://localhost:8000/api/docs/

admin: ## Open Django admin in browser
	open http://localhost:8000/admin/

setup: ## Initial setup (build, up, migrate)
	make build
	make up
	sleep 10
	make migrate
	@echo "Setup complete! Access the API at http://localhost:8000/api/"

dev: ## Development mode with logs
	docker-compose up

monitor: ## Monitor all services with logs
	docker-compose up -d
	docker-compose logs -f 