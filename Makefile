# ─────────────────────────────────────────────────────────────────────────────
# Arquiteto Decisor — atalhos de desenvolvimento
# ─────────────────────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help up down logs ps rebuild test lint smoke clean

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Sobe toda a malha (gateway + serviços + infraestrutura)
	$(COMPOSE) up --build -d
	@echo "Gateway disponível em http://localhost:8080 (docs em /docs)"
	@echo "Painel RabbitMQ em http://localhost:15672 (guest/guest)"

down: ## Derruba a malha e remove a rede
	$(COMPOSE) down

logs: ## Acompanha os logs de todos os serviços
	$(COMPOSE) logs -f

ps: ## Mostra o estado dos contêineres
	$(COMPOSE) ps

rebuild: ## Reconstrói as imagens sem cache
	$(COMPOSE) build --no-cache

smoke: ## Teste de fumaça via gateway (requer a malha no ar)
	@bash scripts/smoke.sh

test: ## Roda os testes de cada serviço (pytest)
	@for svc in api-gateway decisions-service catalog-service notification-service; do \
		echo "▶ testando $$svc"; \
		(cd src/$$svc && python -m pytest -q || exit 1); \
	done

lint: ## Linta o código Python (ruff)
	ruff check src

clean: ## Remove volumes e dados persistidos
	$(COMPOSE) down -v
