.PHONY: help install all smoke integration e2e tags

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

all:  ## Run all tests (smoke + integration + e2e) in a single run
	$(CODER_EVAL) run $(TASKS) -e experiments/e2e.yaml -j 1 -v

smoke:  ## Run all smoke tests
	$(CODER_EVAL) run $(TASKS) -e experiments/default.yaml --tags smoke -j 1 -v

integration:  ## Run all integration tests
	$(CODER_EVAL) run $(TASKS) -e experiments/integration.yaml --tags integration -j 1 -v

e2e:  ## Run all end-to-end tests
	$(CODER_EVAL) run $(TASKS) -e experiments/e2e.yaml --tags e2e -j 1 -v

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
	$(CODER_EVAL) run $(TASKS) -e $(or $(EXPERIMENT),experiments/default.yaml) $(foreach t,$(TAGS),--tags $(t)) -j 1 -v

# Run all tests for a specific skill: make test-uipath-maestro-flow
test-%:  ## Run all tests for a specific skill
	$(CODER_EVAL) run $(shell find tasks/$* -name '*.yaml' -type f) -e experiments/default.yaml -j 1 -v

.DEFAULT_GOAL := help
