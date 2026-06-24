SHELL := /bin/sh

COMPOSE ?= docker compose
API_URL ?= http://localhost:8000
EVAL_API_URL ?= $(API_URL)

.DEFAULT_GOAL := help

.PHONY: help build up up-detached down logs health shell eval eval-static clean-runs

help:
	@printf '%s\n' \
		'Targets:' \
		'  make build        Build the local Docker image' \
		'  make up           Build and run the API in the foreground' \
		'  make up-detached  Build and run the API in the background' \
		'  make down         Stop local compose services' \
		'  make logs         Follow API logs' \
		'  make health       Check GET /health' \
		'  make shell        Open a shell in the app image' \
		'  make eval         Run evals/run_evals.py against the API' \
		'  make eval-static  Run evals in-process and generate static dashboard data' \
		'  make clean-runs   Remove generated local run bundles'

build:
	$(COMPOSE) build

up:
	mkdir -p runs
	$(COMPOSE) up --build

up-detached:
	mkdir -p runs
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f app

health:
	curl -fsS "$(API_URL)/health"

shell:
	$(COMPOSE) run --rm app sh

eval:
	@if [ ! -f evals/run_evals.py ]; then \
		echo 'evals/run_evals.py does not exist yet.'; \
		exit 1; \
	fi
	EVAL_API_URL="$(EVAL_API_URL)" uv run python evals/run_evals.py --fail-on-error

eval-static:
	uv run --prerelease=allow python evals/run_evals.py --offline --fail-on-error

clean-runs:
	rm -rf runs/*
