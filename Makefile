# Project configuration
UV = uv

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

# =============================================================================
# SERVER
# =============================================================================

.PHONY: serve
serve: ## Run FastAPI server with uvicorn
	@echo "$(BLUE)Starting FastAPI server on http://127.0.0.1:8000 ...$(NC)"
	${UV} run uvicorn aipg.server:create_app --factory --host 127.0.0.1 --port 8000 --reload

# =============================================================================
# FRONTEND
# =============================================================================

.PHONY: frontend-dev
frontend-dev: ## Run Next.js frontend (requires node)
	@echo "$(BLUE)Starting Next.js on http://127.0.0.1:3000 ...$(NC)"
	cd frontend && pnpm dev || npm run dev || yarn dev

.PHONY: frontend-build
frontend-build: ## Build Next.js frontend
	cd frontend && pnpm build || npm run build || yarn build

.PHONY: frontend-start
frontend-start: ## Start Next.js production server
	cd frontend && pnpm start || npm run start || yarn start