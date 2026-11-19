SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: help test lint check-math check-security clean bench-all stacks

help: ## Show targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nTargets:\n"} /^[a-zA-Z0-9_%-]+:.*##/ { printf "  %-16s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

stacks: ## List available PoC stack names
	@echo "Topologies: pg17-baseline pg-birep pgedge bucardo citus yugabyte cockroach"

test: ## Run all unit tests
	python3 -m unittest discover -s tests -v

check-math: ## Validate Markdown LaTeX math rules
	python3 -m unittest tests/test_docs_math_syntax.py -v

check-security: ## Validate governance and security rules
	python3 -m unittest tests/test_governance_and_security.py -v

lint: ## Lint Bash scripts and Docker Compose files
	@find . -path './.git' -prune -o -name '*.sh' -type f -print0 | xargs -0 -r bash -n
	@ef=(); [ ! -f .env ] && [ -f .env.example ] && ef=(--env-file .env.example); \
	while IFS= read -r -d '' cfg; do docker compose "$${ef[@]}" -f "$$cfg" config -q; done < <(find . -maxdepth 3 -name 'docker-compose-*.yml' -type f -print0)
	@echo "Lint checks passed."

up-%: ## Start stack <name> from root or stacks/
	@cfg="$$(find . -maxdepth 3 -name 'docker-compose-$*.yml' -print -quit)"; \
	[ -z "$$cfg" ] && cfg="$$(find 'stacks/$*' -maxdepth 1 -name 'docker-compose-*.yml' -print -quit 2>/dev/null || true)"; \
	test -n "$$cfg" || { echo "Missing stack '$*'"; exit 1; }; \
	ef=(); [ ! -f .env ] && [ -f .env.example ] && ef=(--env-file .env.example); \
	docker compose "$${ef[@]}" -f "$$cfg" up -d

down-%: ## Stop stack <name> and remove volumes
	@cfg="$$(find . -maxdepth 3 -name 'docker-compose-$*.yml' -print -quit)"; \
	[ -z "$$cfg" ] && cfg="$$(find 'stacks/$*' -maxdepth 1 -name 'docker-compose-*.yml' -print -quit 2>/dev/null || true)"; \
	test -n "$$cfg" || { echo "Missing stack '$*'"; exit 1; }; \
	ef=(); [ ! -f .env ] && [ -f .env.example ] && ef=(--env-file .env.example); \
	docker compose "$${ef[@]}" -f "$$cfg" down -v

setup-%: ## Run setup script for topology <name>
	@u="$$(echo '$*' | tr '-' '_')"; \
	if [ -f "scripts/setup_$*.sh" ]; then bash "scripts/setup_$*.sh"; \
	elif [ -f "scripts/setup_$${u}.sh" ]; then bash "scripts/setup_$${u}.sh"; \
	elif [ "$*" = "pg-birep" ] || [ "$*" = "pg_birep" ]; then bash "scripts/setup_birep.sh"; \
	else s="$$(find 'stacks/$*' -maxdepth 1 -name 'setup_*.sh' -print -quit 2>/dev/null || true)"; \
	test -n "$$s" && bash "$$s" || { echo "No setup script for '$*'"; exit 1; }; fi

test-%: ## Run tests for topology <name>
	@u="$$(echo '$*' | tr '-' '_')"; \
	if [ -f "tests/test_$*.sh" ]; then bash "tests/test_$*.sh"; \
	elif [ -f "scripts/test_$*.sh" ]; then bash "scripts/test_$*.sh"; \
	elif [ -f "scripts/test_$${u}.sh" ]; then bash "scripts/test_$${u}.sh"; \
	elif [ -f "tests/test_$*.py" ]; then python3 -m unittest "tests/test_$*.py" -v; \
	else echo "No test runner for '$*'"; exit 1; fi

bench-all: ## Run scripts/bench_*.sh hooks
	@shopt -s nullglob; hooks=(scripts/bench_*.sh); \
	if [ $${#hooks[@]} -eq 0 ]; then echo "No benchmark hooks registered yet."; \
	else for h in "$${hooks[@]}"; do bash "$$h"; done; fi

clean: ## Clean caches, logs, and generated reports
	python3 -c "import pathlib,shutil;[shutil.rmtree(p,ignore_errors=True) for p in pathlib.Path('.').rglob('*') if p.name in {'__pycache__','.pytest_cache'}]"
	rm -f reports/*.html *.log
