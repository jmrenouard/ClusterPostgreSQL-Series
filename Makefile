SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: help test lint check-security clean bench-all

help: ## Show targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nTargets:\n"} /^[a-zA-Z0-9_%-]+:.*##/ { printf "  %-16s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

test: ## Run all unit tests
	python3 -m unittest discover -s tests -v

check-security: ## Validate governance and security rules
	python3 -m unittest tests/test_governance_and_security.py -v

lint: ## Lint Bash scripts and Docker Compose files
	@find . -path './.git' -prune -o -name '*.sh' -type f -print0 | xargs -0 -r bash -n
	@ef=(); [ ! -f .env ] && [ -f .env.example ] && ef=(--env-file .env.example); \
	while IFS= read -r -d '' cfg; do docker compose "$${ef[@]}" -f "$$cfg" config -q; done < <(find . -maxdepth 3 -name 'docker-compose-*.yml' -type f -print0)
	@echo "Lint checks passed."

up-%: ## Start docker-compose-<name>.yml
	@test -f "docker-compose-$*.yml" || { echo "Missing docker-compose-$*.yml"; exit 1; }
	@docker compose -f "docker-compose-$*.yml" up -d

down-%: ## Stop docker-compose-<name>.yml and remove volumes
	@test -f "docker-compose-$*.yml" || { echo "Missing docker-compose-$*.yml"; exit 1; }
	@docker compose -f "docker-compose-$*.yml" down -v

test-%: ## Run tests for topology <name>
	@if [ -f "tests/test_$*.sh" ]; then bash "tests/test_$*.sh"; \
	elif [ -f "tests/test_$*.py" ]; then python3 -m unittest "tests/test_$*.py" -v; \
	else echo "No test runner for '$*'"; exit 1; fi

bench-all: ## Run scripts/bench_*.sh hooks
	@shopt -s nullglob; hooks=(scripts/bench_*.sh); \
	if [ $${#hooks[@]} -eq 0 ]; then echo "No benchmark hooks registered yet."; \
	else for h in "$${hooks[@]}"; do bash "$$h"; done; fi

clean: ## Clean caches, logs, and generated reports
	python3 -c "import pathlib,shutil;[shutil.rmtree(p,ignore_errors=True) for p in pathlib.Path('.').rglob('*') if p.name in {'__pycache__','.pytest_cache'}]"
	rm -f reports/*.html *.log
