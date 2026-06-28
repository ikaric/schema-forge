SHELL := /bin/bash

UV ?= uv
PORT ?= 8000
HOST ?= 127.0.0.1
NETLIST ?= design/netlists/main.cir

.PHONY: help init setup build serve dev frontend-dev seed-fuzzface seed-overdrive sim test lint format typecheck check clean

help:
	@echo "Setup:"
	@echo "  init          One-time per-clone identity setup (git author + placeholders)"
	@echo "  setup         Install backend (uv) and frontend (npm) dependencies"
	@echo ""
	@echo "Run (always-on UI on http://$(HOST):$(PORT)):"
	@echo "  dev           Build the SPA and serve it + API + live WebSocket (reload)"
	@echo "  serve         Serve the already-built SPA + API (no reload)"
	@echo "  build         Build the React SPA into the backend static dir"
	@echo "  frontend-dev  Vite dev server on :5173 (proxies to the backend) for UI hacking"
	@echo ""
	@echo "Design loop:"
	@echo "  seed-fuzzface  Load the Fuzz Face design target (the go-to test; no netlist)"
	@echo "  seed-overdrive Load the worked overdrive example (ships a netlist)"
	@echo "  sim            Run a netlist through ngspice + assert vs spec"
	@echo "                   make sim NETLIST=design/netlists/<name>.cir"
	@echo ""
	@echo "Quality:"
	@echo "  test lint format typecheck check clean"

init:
	@command -v python3 >/dev/null 2>&1 || { echo "error: python3 is required" >&2; exit 1; }
	@python3 scripts/init.py

setup:
	$(UV) sync --extra dev
	cd frontend && npm install

build:
	cd frontend && npm run build

serve:
	$(UV) run uvicorn schema_forge.api.asgi:app --host $(HOST) --port $(PORT)

dev: build
	$(UV) run uvicorn schema_forge.api.asgi:app --host $(HOST) --port $(PORT) --reload

frontend-dev:
	cd frontend && npm run dev

seed-fuzzface:
	$(UV) run python scripts/seed_example.py fuzzface

seed-overdrive:
	$(UV) run python scripts/seed_example.py overdrive

sim:
	$(UV) run python -m schema_forge.sim run $(NETLIST) --spec design/spec.md

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check backend

format:
	$(UV) run ruff format backend

typecheck:
	$(UV) run mypy backend/src

check: lint typecheck test

clean:
	rm -rf .venv backend/src/schema_forge/static frontend/node_modules frontend/dist \
	  .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov \
	  $$(find . -type d -name __pycache__)
