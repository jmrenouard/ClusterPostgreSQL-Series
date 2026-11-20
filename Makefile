SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help
export PYTHONDONTWRITEBYTECODE := 1

MDB_DIR ?= env/multi-db-docker-env
PG_STACKS := pg17-baseline pg-streaming pg-logical pg-birep pgedge bucardo citus cockroach yugabyte pg18-streaming pg18-logical pg18-birep yt-cluster

.PHONY: help init-env stacks test check-math check-security lint charts popularity dashboard test-pg-extended bench-all bench-pg18 bench-yt-cluster clean

help: ## Show targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nTargets:\n"} /^[a-zA-Z0-9_%-]+:.*##/ { printf "  %-18s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

init-env: ## Initialize and update the multi-db-docker-env Git submodule
	git submodule update --init --recursive

stacks: ## List available PostgreSQL PoC topologies in $(MDB_DIR)
	@echo "Topologies ($(MDB_DIR)): $(PG_STACKS)"

test: ## Run all unit tests
	python3 -m unittest discover -s tests -v

check-math: ## Validate Markdown LaTeX math rules
	python3 -m unittest tests/test_docs_math_syntax.py -v

check-security: ## Validate governance and security rules
	python3 -m unittest tests/test_governance_and_security.py -v

charts: ## Regenerate all 10 Log10 PNG charts in assets/charts/
	python3 scripts/generate_charts.py
	python3 scripts/generate_charts_v3.py

popularity: ## Collect live GitHub ecosystem popularity telemetry into results/project_popularity.csv
	python3 scripts/collect_popularity.py

dashboard: ## Rebuild offline HTML benchmark explorer bundles in dashboard/
	python3 scripts/build_dashboard.py

lint: ## Lint repo Bash scripts and all 13 submodule PostgreSQL Compose files
	@find . \( -path './.git' -o -path './env' \) -prune -o -name '*.sh' -type f -print0 | xargs -0 -r bash -n
	@ef=(); [ ! -f .env ] && [ -f .env.example ] && ef=(--env-file .env.example); \
	while IFS= read -r -d '' cfg; do docker compose "$${ef[@]}" -f "$$cfg" config -q; done < <(find . -maxdepth 3 \( -path './.git' -o -path './env' \) -prune -o -name 'docker-compose-*.yml' -type f -print0)
	@if [ -d "$(MDB_DIR)" ]; then \
		mef=(); [ -f "$(MDB_DIR)/.env" ] && mef=(--env-file "$(MDB_DIR)/.env") || { [ -f "$(MDB_DIR)/.env.example" ] && mef=(--env-file "$(MDB_DIR)/.env.example"); }; \
		for s in $(PG_STACKS); do \
			cfg="$(MDB_DIR)/docker-compose-$${s}.yml"; \
			test -f "$$cfg" || { echo "Missing submodule compose file: $$cfg"; exit 1; }; \
			docker compose "$${mef[@]}" -f "$$cfg" config -q; \
		done; \
	fi
	@echo "Lint checks passed."

up-%: ## Start stack <name> via $(MDB_DIR)
	@cfg="$(MDB_DIR)/docker-compose-$*.yml"; \
	test -f "$$cfg" || { echo "Missing stack '$$cfg' (run 'make init-env' first)"; exit 1; }; \
	ef=(); [ -f .env ] && ef=(--env-file .env) || { [ -f "$(MDB_DIR)/.env" ] && ef=(--env-file "$(MDB_DIR)/.env") || { [ -f "$(MDB_DIR)/.env.example" ] && ef=(--env-file "$(MDB_DIR)/.env.example"); }; }; \
	docker compose "$${ef[@]}" -f "$$cfg" up -d

down-%: ## Stop stack <name> via $(MDB_DIR) and remove volumes
	@cfg="$(MDB_DIR)/docker-compose-$*.yml"; \
	test -f "$$cfg" || { echo "Missing stack '$$cfg' (run 'make init-env' first)"; exit 1; }; \
	ef=(); [ -f .env ] && ef=(--env-file .env) || { [ -f "$(MDB_DIR)/.env" ] && ef=(--env-file "$(MDB_DIR)/.env") || { [ -f "$(MDB_DIR)/.env.example" ] && ef=(--env-file "$(MDB_DIR)/.env.example"); }; }; \
	docker compose "$${ef[@]}" -f "$$cfg" down -v

setup-%: ## Run setup script for topology <name> via $(MDB_DIR)
	@u="$$(echo '$*' | tr '-' '_')"; \
	s="$$(find "$(MDB_DIR)/scripts/$${u}" -maxdepth 1 -name 'setup_*.sh' -print -quit 2>/dev/null || true)"; \
	if [ -n "$$s" ]; then (cd "$(MDB_DIR)" && bash "$${s#$(MDB_DIR)/}"); \
	elif [ -f "scripts/setup_$${u}.sh" ]; then bash "scripts/setup_$${u}.sh"; \
	else echo "No setup script for '$*'"; exit 1; fi

test-pg-extended: ## Run extended 18-test PostgreSQL matrix (T11-T18) via $(MDB_DIR)
	@test -f "$(MDB_DIR)/scripts/test_pg_extended_matrix.sh" || { echo "Submodule missing; run 'make init-env' first."; exit 1; }
	(cd "$(MDB_DIR)" && bash scripts/test_pg_extended_matrix.sh)

test-%: ## Run functional/limit test suite for topology <name> via $(MDB_DIR)
	@u="$$(echo '$*' | tr '-' '_')"; \
	if [ -f "$(MDB_DIR)/tests/test_$${u}.sh" ]; then (cd "$(MDB_DIR)" && bash "tests/test_$${u}.sh"); \
	elif [ -f "scripts/test_$${u}.sh" ]; then bash "scripts/test_$${u}.sh"; \
	elif [ -f "tests/test_$${u}.py" ]; then python3 -m unittest "tests/test_$${u}.py" -v; \
	elif [ -f "tests/test_$*.py" ]; then python3 -m unittest "tests/test_$*.py" -v; \
	else echo "No test runner for '$*'"; exit 1; fi

bench-all: ## Run V1 + V2 PostgreSQL benchmark suites via $(MDB_DIR) and rebuild charts & dashboard
	@test -d "$(MDB_DIR)" || { echo "Submodule missing; run 'make init-env' first."; exit 1; }
	BENCH_OUT_DIR="$(CURDIR)/results" bash "$(MDB_DIR)/scripts/bench_pg_multimaster.sh"
	BENCH_OUT_DIR="$(CURDIR)/results" bash "$(MDB_DIR)/scripts/bench_pg_v2_runner.sh"
	$(MAKE) charts dashboard

bench-pg18: ## Run PostgreSQL 18.6 benchmark suite via $(MDB_DIR) and rebuild charts & dashboard
	@test -d "$(MDB_DIR)" || { echo "Submodule missing; run 'make init-env' first."; exit 1; }
	BENCH_OUT_DIR="$(CURDIR)/results" bash "$(MDB_DIR)/scripts/bench_pg18_runner.sh"
	$(MAKE) charts dashboard

bench-yt-cluster: ## Run YT Cluster 1.21.3 benchmark suite via $(MDB_DIR) and rebuild charts & dashboard
	@test -d "$(MDB_DIR)" || { echo "Submodule missing; run 'make init-env' first."; exit 1; }
	BENCH_OUT_DIR="$(CURDIR)/results" bash "$(MDB_DIR)/scripts/bench_yt_runner.sh"
	$(MAKE) charts dashboard

clean: ## Clean caches, logs, and generated reports
	python3 -c "import pathlib,shutil;[shutil.rmtree(p,ignore_errors=True) for p in pathlib.Path('.').rglob('*') if p.name in {'__pycache__','.pytest_cache'} and 'env' not in p.parts]"
	rm -f reports/*.html *.log
