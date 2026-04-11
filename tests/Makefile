.PHONY: help install all smoke integration e2e

SKILLS_REPO_PATH ?= $(shell cd .. && pwd)
VENV := .venv
CODER_EVAL := SKILLS_REPO_PATH=$(SKILLS_REPO_PATH) $(VENV)/bin/coder-eval
TASKS := $(shell find tasks -name '*.yaml' -type f)

help:  ## Show available commands
	@grep -E '^[a-zA-Z0-9_%-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install coder-eval into local .venv (requires Python 3.13+)
	uv venv --python 3.13 $(VENV)
	uv pip install --python $(VENV)/bin/python "coder-eval @ git+https://github.com/UiPath/coder_eval.git"
	@echo ""
	@echo "See https://github.com/UiPath/coder_eval for environment setup (.env, API keys, etc.)"

all: smoke integration e2e  ## Run all tests (smoke + integration + e2e)

smoke:  ## Run all smoke tests
	$(CODER_EVAL) run $(TASKS) -e experiments/default.yaml --tags smoke -j 1 -v

integration:  ## Run all integration tests
	$(CODER_EVAL) run $(TASKS) -e experiments/integration.yaml --tags integration -j 1 -v

e2e:  ## Run all end-to-end tests
	$(CODER_EVAL) run $(TASKS) -e experiments/e2e.yaml --tags e2e -j 1 -v

# Run all tests for a specific skill: make test-uipath-maestro-flow
test-%:  ## Run all tests for a specific skill
	$(CODER_EVAL) run $(shell find tasks/$* -name '*.yaml' -type f) -e experiments/default.yaml -j 1 -v

.DEFAULT_GOAL := help
