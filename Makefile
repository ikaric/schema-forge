SHELL := /bin/bash

UV ?= uv
PORT ?= 8000
HOST ?= 127.0.0.1
NETLIST ?= design/netlists/main.cir

.PHONY: help init setup build serve dev up down frontend-dev sim test lint format typecheck check clean

help:
	@echo "Setup:"
	@echo "  init          One-time per-clone identity setup (git author + placeholders)"
	@echo "  setup         Install backend (uv) and frontend (npm) dependencies"
	@echo ""
	@echo "Run (always-on UI on http://$(HOST):$(PORT)):"
	@echo "  up            Build + serve detached in the background (live UI; survives the shell)"
	@echo "  down          Stop the background server started by 'make up'"
	@echo "  dev           Build the SPA and serve it + API + live WebSocket (foreground, reload)"
	@echo "  serve         Serve the already-built SPA + API (foreground, no reload)"
	@echo "  build         Build the React SPA into the backend static dir"
	@echo "  frontend-dev  Vite dev server on :5173 (proxies to the backend) for UI hacking"
	@echo ""
	@echo "Design loop (after /target):"
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

# Detached "always-on" UI: build once, then serve in the background so the live
# dashboard stays up without holding a terminal open. Idempotent — a no-op if it
# is already serving. No --reload: the in-app watcher streams design/ over the WS.
up:
	@if curl -fsS http://$(HOST):$(PORT)/api/health >/dev/null 2>&1; then \
	  echo "schema-forge already live at http://$(HOST):$(PORT)"; \
	else \
	  ( cd frontend && npm run build ); \
	  mkdir -p .claude/local; \
	  nohup .venv/bin/uvicorn schema_forge.api.asgi:app --host $(HOST) --port $(PORT) \
	    >> .claude/local/server.log 2>&1 < /dev/null & \
	  echo $$! > .claude/local/server.pid; \
	  echo "schema-forge serving (detached, pid $$(cat .claude/local/server.pid)) at http://$(HOST):$(PORT) — logs: .claude/local/server.log"; \
	fi

down:
	@pid=$$(cat .claude/local/server.pid 2>/dev/null); \
	[ -n "$$pid" ] && kill $$pid 2>/dev/null || true; \
	portpid=$$(lsof -ti tcp:$(PORT) 2>/dev/null); \
	[ -n "$$portpid" ] && kill $$portpid 2>/dev/null || true; \
	rm -f .claude/local/server.pid; \
	echo "schema-forge stopped (was pid $${pid:-none})"

frontend-dev:
	cd frontend && npm run dev

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
