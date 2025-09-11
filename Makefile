# Project configuration
UV = uv

# Platform detection for cross-platform compatibility
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    PLATFORM = mac
    TIMEOUT_CMD = gtimeout
    SHELL_CHECK = command -v gtimeout >/dev/null 2>&1 || (echo "$(YELLOW)Installing coreutils for Mac compatibility...$(NC)" && brew install coreutils)
else
    PLATFORM = linux
    TIMEOUT_CMD = timeout
    SHELL_CHECK = :
endif

# Colors for output
BLUE = \033[34m
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
NC = \033[0m # No Color

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Project Commands$(NC)"
	@echo "$(BLUE)========================$(NC)"
	@echo "$(GREEN)Development Workflow:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { if ($$1 !~ /^docker-/ && $$1 !~ /^help$$/) printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^docker-[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# =============================================================================
# CODE QUALITY
# =============================================================================

.PHONY: lint
lint: ## Run linting with ruff
	@echo "$(BLUE)Running linter...$(NC)"
	${UV} run ruff check .

.PHONY: lint-fix
lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	${UV} run ruff check --fix .

.PHONY: format
format: ## Format code and organize imports with ruff
	@echo "$(BLUE)Formatting code and organizing imports...$(NC)"
	${UV} run ruff check --select I --fix .
	${UV} run ruff format .

.PHONY: quality
quality: format lint-fix ## Run all quality checks
	@echo "$(GREEN)All quality checks completed!$(NC)"

pre-commit-install:
	pre-commit install
pre-commit-run:
	pre-commit run --all-files
pre-commit: pre-commit-install pre-commit-run

# =============================================================================
# DOCKER
# =============================================================================

.PHONY: docker-build-sandbox
docker-build-sandbox: ## Build the custom Python sandbox Docker image with preinstalled libraries
	@echo "$(BLUE)Building custom Python sandbox image...$(NC)"
	docker build -f docker/Dockerfile.sandbox -t aipg-sandbox:latest .
	@echo "$(GREEN)Sandbox image built successfully!$(NC)"

.PHONY: docker-build-api
docker-build-api: ## Build the API Docker image
	@echo "$(BLUE)Building API image...$(NC)"
	docker build -f docker/Dockerfile.api -t aipg-api:latest .
	@echo "$(GREEN)API image built successfully!$(NC)"

.PHONY: docker-build-frontend
docker-build-frontend: ## Build the frontend Docker image
	@echo "$(BLUE)Building frontend image...$(NC)"
	docker build -f docker/Dockerfile.frontend -t aipg-frontend:latest .
	@echo "$(GREEN)Frontend image built successfully!$(NC)"

.PHONY: docker-build
docker-build: docker-build-sandbox docker-build-api docker-build-frontend ## Build all Docker images
	@echo "$(GREEN)All Docker images built successfully!$(NC)"

# =============================================================================
# DOCKER COMPOSE COMMANDS
# =============================================================================

.PHONY: docker-up
docker-up: ## Start all services in production mode
	@echo "$(BLUE)Starting all services in production mode...$(NC)"
	docker compose up -d
	@echo "$(GREEN)All services started! Visit http://localhost$(NC)"

.PHONY: docker-up-dev
docker-up-dev: ## Start all services in development mode with hot reload
	@echo "$(BLUE)Starting all services in development mode...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Development services started!$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:5173$(NC)"

.PHONY: docker-up-prod
docker-up-prod: ## Start all services in production mode with production overrides
	@echo "$(BLUE)Starting all services in production mode...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Production services started! Visit http://localhost$(NC)"

.PHONY: docker-down
docker-down: ## Stop and remove all containers
	@echo "$(BLUE)Stopping and removing all containers...$(NC)"
	docker compose down
	@echo "$(GREEN)All containers stopped and removed!$(NC)"

.PHONY: docker-down-dev
docker-down-dev: ## Stop and remove development containers
	@echo "$(BLUE)Stopping development containers...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down
	@echo "$(GREEN)Development containers stopped!$(NC)"

.PHONY: docker-down-prod
docker-down-prod: ## Stop and remove production containers
	@echo "$(BLUE)Stopping production containers...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "$(GREEN)Production containers stopped!$(NC)"

.PHONY: docker-restart
docker-restart: docker-down docker-up ## Restart all services
	@echo "$(GREEN)All services restarted!$(NC)"

.PHONY: docker-restart-dev
docker-restart-dev: docker-down-dev docker-up-dev ## Restart development services
	@echo "$(GREEN)Development services restarted!$(NC)"

.PHONY: docker-logs
docker-logs: ## Show logs from all services
	@echo "$(BLUE)Showing logs from all services...$(NC)"
	docker compose logs -f

.PHONY: docker-logs-api
docker-logs-api: ## Show logs from API service
	@echo "$(BLUE)Showing API logs...$(NC)"
	docker compose logs -f api

.PHONY: docker-logs-frontend
docker-logs-frontend: ## Show logs from frontend service
	@echo "$(BLUE)Showing frontend logs...$(NC)"
	docker compose logs -f frontend

.PHONY: docker-logs-sandbox
docker-logs-sandbox: ## Show logs from sandbox service
	@echo "$(BLUE)Showing sandbox logs...$(NC)"
	docker compose logs -f sandbox

.PHONY: docker-ps
docker-ps: ## Show status of all containers
	@echo "$(BLUE)Container status:$(NC)"
	docker compose ps

.PHONY: docker-exec-api
docker-exec-api: ## Execute shell in API container
	@echo "$(BLUE)Connecting to API container...$(NC)"
	@docker compose exec api bash || docker compose exec api sh

.PHONY: docker-exec-sandbox
docker-exec-sandbox: ## Execute shell in sandbox container
	@echo "$(BLUE)Connecting to sandbox container...$(NC)"
	@docker compose exec sandbox bash || docker compose exec sandbox sh

# =============================================================================
# DOCKER CLEANUP COMMANDS
# =============================================================================

.PHONY: docker-clean
docker-clean: ## Remove all stopped containers, unused networks, images, and build cache
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	docker system prune -af
	@echo "$(GREEN)Docker cleanup completed!$(NC)"

.PHONY: docker-clean-volumes
docker-clean-volumes: docker-down ## Remove all containers and volumes (WARNING: This will delete all data!)
	@echo "$(RED)WARNING: This will delete all Docker volumes and data!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	@docker compose down -v
	@docker volume prune -f
	@echo "$(GREEN)All volumes cleaned!$(NC)"

.PHONY: docker-clean-cache
docker-clean-cache: ## Remove database and LLM cache from running containers
	@echo "$(BLUE)Cleaning database and LLM cache...$(NC)"
	@if docker compose ps --format json | grep -q '"Service":"api".*"State":"running"'; then \
		echo "$(YELLOW)Removing ChromaDB database cache...$(NC)"; \
		docker compose exec api sh -c 'rm -rf /app/aipg/cache/chroma/*' || true; \
		echo "$(YELLOW)Removing LLM cache...$(NC)"; \
		docker compose exec api sh -c 'rm -rf /app/aipg/cache/llm/*' || true; \
		echo "$(GREEN)Cache cleaned successfully!$(NC)"; \
	else \
		echo "$(RED)API container is not running. Start services first with 'make docker-up'$(NC)"; \
		exit 1; \
	fi

.PHONY: docker-clean-cache-volumes
docker-clean-cache-volumes: docker-down ## Remove cache volumes completely (WARNING: This will delete all cache data!)
	@echo "$(RED)WARNING: This will delete all cache data including ChromaDB and LLM cache!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	@echo "$(BLUE)Removing cache volumes...$(NC)"
	@docker volume rm ai-micro-project-generator_cache_data 2>/dev/null || true
	@docker volume rm ai-micro-project-generator_cache_dev_data 2>/dev/null || true
	@echo "$(GREEN)Cache volumes removed!$(NC)"

.PHONY: docker-inspect-cache
docker-inspect-cache: ## Show cache directory contents and sizes
	@echo "$(BLUE)Inspecting cache contents...$(NC)"
	@if docker compose ps --format json | grep -q '"Service":"api".*"State":"running"'; then \
		echo "$(YELLOW)Cache directory structure:$(NC)"; \
		docker compose exec api find /app/aipg/cache -type f | head -20 || true; \
		echo ""; \
		echo "$(YELLOW)Cache sizes:$(NC)"; \
		docker compose exec api sh -c 'for dir in /app/aipg/cache/*; do [ -d "$$dir" ] && du -sh "$$dir"; done' 2>/dev/null || echo "  No cache directories found"; \
		echo ""; \
		echo "$(YELLOW)Total cache size:$(NC)"; \
		docker compose exec api du -sh /app/aipg/cache 2>/dev/null || echo "  Cache directory not found"; \
	else \
		echo "$(RED)API container is not running. Start services first with 'make docker-up'$(NC)"; \
		exit 1; \
	fi

.PHONY: docker-rebuild
docker-rebuild: docker-down docker-clean docker-build docker-up ## Full rebuild: stop, clean, rebuild, and start
	@echo "$(GREEN)Full rebuild completed!$(NC)"

.PHONY: docker-rebuild-dev
docker-rebuild-dev: docker-down-dev docker-build docker-up-dev ## Full rebuild for development
	@echo "$(GREEN)Development rebuild completed!$(NC)"

# =============================================================================
# DOCKER HEALTH CHECK COMMANDS
# =============================================================================

.PHONY: docker-health
docker-health: ## Check health status of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

.PHONY: docker-wait-healthy
docker-wait-healthy: ## Wait for all services to be healthy (cross-platform compatible)
	@echo "$(BLUE)Waiting for all services to be healthy (Platform: $(PLATFORM))...$(NC)"
	@$(SHELL_CHECK)
	@if command -v $(TIMEOUT_CMD) >/dev/null 2>&1; then \
		$(TIMEOUT_CMD) 120 bash -c 'until docker compose ps | grep -q "healthy"; do sleep 2; done' || (echo "$(RED)Timeout waiting for services to be healthy$(NC)" && exit 1); \
	else \
		echo "$(YELLOW)Timeout command not available, checking health status manually...$(NC)"; \
		for i in $$(seq 1 60); do \
			if docker compose ps | grep -q "healthy"; then break; fi; \
			sleep 2; \
		done; \
		if ! docker compose ps | grep -q "healthy"; then \
			echo "$(RED)Services not healthy after 120 seconds$(NC)" && exit 1; \
		fi; \
	fi
	@echo "$(GREEN)All services are healthy!$(NC)"

.PHONY: docker-platform-info
docker-platform-info: ## Show platform and Docker version information
	@echo "$(BLUE)Platform Information:$(NC)"
	@echo "  OS: $(UNAME_S)"
	@echo "  Platform: $(PLATFORM)"
	@echo "  Timeout command: $(TIMEOUT_CMD)"
	@echo ""
	@echo "$(BLUE)Docker Information:$(NC)"
	@docker --version
	@docker compose version
	@echo ""
	@echo "$(BLUE)Make Information:$(NC)"
	@$(MAKE) --version | head -1
