.PHONY: help install check fmt lint all smoke integration e2e tags

SKILLS_REPO_PATH ?= $(shell cd .. && pwd)
VENV := .venv
PYTHON_VERSION ?= 3.13
CODER_EVAL_PACKAGE ?= coder-eval @ git+https://github.com/UiPath/coder_eval.git
CODER_EVAL_BIN := $(VENV)/bin/coder-eval
CODER_EVAL := SKILLS_REPO_PATH=$(SKILLS_REPO_PATH) $(CODER_EVAL_BIN)
RUFF ?= uvx ruff
TASKS := $(shell find tasks -name '*.yaml' -type f)
TASK_PARALLELISM ?= 1

help:  ## Show available commands
	@grep -E '^[a-zA-Z0-9_%-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install coder-eval into local .venv (requires Python 3.13+ and the UiPath ml-packages feed)
	@if [ -z "$$UV_EXTRA_INDEX_URL" ] && { [ -z "$$UV_INDEX_UIPATH_USERNAME" ] || [ -z "$$UV_INDEX_UIPATH_PASSWORD" ]; }; then \
	  echo "ERROR: coder-eval currently requires packages from the UiPath ml-packages feed."; \
	  echo "Set UV_EXTRA_INDEX_URL, or set both UV_INDEX_UIPATH_USERNAME and UV_INDEX_UIPATH_PASSWORD."; \
	  exit 2; \
	fi
	uv venv --python $(PYTHON_VERSION) $(VENV)
	@if [ -n "$$UV_EXTRA_INDEX_URL" ]; then \
	  echo "Using UV_EXTRA_INDEX_URL for additional package resolution."; \
	  uv pip install --python $(VENV)/bin/python "$(CODER_EVAL_PACKAGE)"; \
	elif [ -n "$$UV_INDEX_UIPATH_USERNAME" ] && [ -n "$$UV_INDEX_UIPATH_PASSWORD" ]; then \
	  echo "Using UiPath private PyPI feed (ml-packages)."; \
	  UV_EXTRA_INDEX_URL="https://$$UV_INDEX_UIPATH_USERNAME:$$UV_INDEX_UIPATH_PASSWORD@uipath.pkgs.visualstudio.com/_packaging/ml-packages/pypi/simple/" \
	    uv pip install --python $(VENV)/bin/python "$(CODER_EVAL_PACKAGE)"; \
	fi
	@echo ""
	@echo "See https://github.com/UiPath/coder_eval for environment setup (.env, API keys, etc.)"

check: fmt lint  ## Run local format and lint checks for test helper scripts

fmt:  ## Check Python formatting under tests/
	$(RUFF) format --check .

lint:  ## Lint Python helper scripts under tests/
	$(RUFF) check .

all:  ## Run all tests (smoke + integration + e2e) in a single run
	$(CODER_EVAL) run $(TASKS) -e experiments/e2e.yaml -j $(TASK_PARALLELISM) -v

smoke:  ## Run all smoke tests
	$(CODER_EVAL) run $(TASKS) -e experiments/default.yaml --tags smoke -j $(TASK_PARALLELISM) -v

integration:  ## Run all integration tests
	$(CODER_EVAL) run $(TASKS) -e experiments/integration.yaml --tags integration -j $(TASK_PARALLELISM) -v

e2e:  ## Run all end-to-end tests
	$(CODER_EVAL) run $(TASKS) -e experiments/e2e.yaml --tags e2e -j $(TASK_PARALLELISM) -v

tags:  ## Run tests matching one or more tags: make tags TAGS="integration connector-feature" [EXPERIMENT=experiments/integration.yaml]
	@if [ -z "$(TAGS)" ]; then echo "Usage: make tags TAGS=\"tag1 tag2\" [EXPERIMENT=experiments/<file>.yaml]"; exit 2; fi
	@TAGS="$(TAGS)" python3 -c 'import os,re,sys,glob; \
wanted=set(os.environ["TAGS"].split()); \
files=sorted(glob.glob("tasks/**/*.yaml", recursive=True)); \
matches=[]; \
[matches.append(f) for f in files if (lambda m: m and wanted.issubset({t.strip() for t in m.group(1).split(",")}))(re.search(r"^tags:\s*\[([^\]]+)\]", open(f).read(), re.M))]; \
print(f"Matched {len(matches)} task(s) for tags: {sorted(wanted)}"); \
[print(f"  - {m}") for m in matches]; \
sys.exit(0 if matches else 3)'
	$(CODER_EVAL) run $(TASKS) -e $(or $(EXPERIMENT),experiments/default.yaml) $(foreach t,$(TAGS),--tags $(t)) -j $(TASK_PARALLELISM) -v

# Run all tests for a specific skill: make test-uipath-maestro-flow
test-%:  ## Run all tests for a specific skill
	$(CODER_EVAL) run $(shell find tasks/$* -name '*.yaml' -type f) -e experiments/default.yaml -j $(TASK_PARALLELISM) -v

.DEFAULT_GOAL := help
