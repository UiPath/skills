.PHONY: help install all smoke smoke_rpa e2e tags

SKILLS_REPO_PATH ?= $(shell cd .. && pwd)
VENV := .venv
CODER_EVAL := SKILLS_REPO_PATH=$(SKILLS_REPO_PATH) $(VENV)/bin/coder-eval
TASKS := $(shell find tasks -name '*.yaml' -type f)
TASK_PARALLELISM ?= 1
# Same pin and agent image CI uses (tests/.coder-eval-version).
CE_VERSION := $(shell tr -d '[:space:]' < .coder-eval-version)
CE_IMAGE := ghcr.io/uipath/coder-eval-agent:$(CE_VERSION)
CE_CONSTRAINTS := $(VENV)/ce-constraints.txt

help:  ## Show available commands
	@grep -E '^[a-zA-Z0-9_%-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install pinned coder-eval into local .venv, constrained to the agent image's deps (requires Python 3.13+ and Docker; UV_INDEX_UIPATH_USERNAME/PASSWORD optional for private ml-packages feed)
	uv venv --python 3.13 $(VENV)
	@# Constrain to the deps frozen into the pinned agent image, as CI does, so
	@# local runs resolve what smoke/ad-hoc/nightly resolve. No Docker -> an
	@# empty constraints file (valid, unconstrained) plus a warning. The image is
	@# amd64-only, hence --platform (emulated on Apple Silicon).
	@if docker run --rm --platform linux/amd64 --entrypoint pip $(CE_IMAGE) freeze --exclude-editable > $(CE_CONSTRAINTS).raw; then \
	  grep -vE '^coder-eval| @ ' $(CE_CONSTRAINTS).raw > $(CE_CONSTRAINTS) || true; \
	  echo "Constraining to $(CE_IMAGE)."; \
	else \
	  : > $(CE_CONSTRAINTS); \
	  echo "WARNING: could not read $(CE_IMAGE) (Docker not running?) — installing without image constraints."; \
	fi; \
	rm -f $(CE_CONSTRAINTS).raw
	@if [ -n "$$UV_INDEX_UIPATH_USERNAME" ] && [ -n "$$UV_INDEX_UIPATH_PASSWORD" ]; then \
	  echo "Using UiPath private PyPI feed (ml-packages)."; \
	  export UV_EXTRA_INDEX_URL="https://$$UV_INDEX_UIPATH_USERNAME:$$UV_INDEX_UIPATH_PASSWORD@uipath.pkgs.visualstudio.com/_packaging/ml-packages/pypi/simple/"; \
	else \
	  echo "UV_INDEX_UIPATH_USERNAME/PASSWORD not set — installing without the UiPath private PyPI feed."; \
	  echo "Set both variables before running 'make install' if you need packages from the ml-packages feed."; \
	fi; \
	uv pip install --python $(VENV)/bin/python --prerelease=allow -c $(CE_CONSTRAINTS) \
	  "coder-eval[litellm,harbor,codex]==$(CE_VERSION)"
	@echo ""
	@echo "See https://github.com/UiPath/coder_eval for environment setup (.env, API keys, etc.)"
	@echo "checker_context.api_route defaults llm_judge to litellm -> gpt-5.6-luna (see tests/README.md#checker-context)."
	@echo "Set CODEX_BASE_URL/CODEX_API_KEY in your env before running tasks locally."

all:  ## Run all tests in a single run (uses the full default budget)
	$(CODER_EVAL) run $(TASKS) -e experiments/default.yaml -j $(TASK_PARALLELISM) -v

smoke:  ## Run all smoke tests (Linux, docker)
	$(CODER_EVAL) run $(TASKS) -e experiments/smoke.yaml --tags smoke -j $(TASK_PARALLELISM) -v

smoke_rpa:  ## Run all Windows RPA smoke tests (tempdir)
	$(CODER_EVAL) run $(TASKS) -e experiments/smoke-windows.yaml --tags smoke -j $(TASK_PARALLELISM) -v

e2e:  ## Run all end-to-end tests
	$(CODER_EVAL) run $(TASKS) -e experiments/default.yaml --tags e2e -j $(TASK_PARALLELISM) -v

tags:  ## Run tests matching one or more tags: make tags TAGS="connector-feature" [EXPERIMENT=experiments/default.yaml]
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
