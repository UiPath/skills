.PHONY: help install e2e e2e-flow

SKILLS_REPO_PATH ?= $(shell cd .. && pwd)

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install coder-eval from GitHub
	uv pip install "coder-eval @ git+https://github.com/UiPath/coder_eval.git"

e2e:  ## Run all skill e2e tests (smoke)
	SKILLS_REPO_PATH=$(SKILLS_REPO_PATH) \
	  coder-eval run tasks/**/*.yaml \
	  -e experiments/default.yaml --tags smoke -j 1

e2e-flow:  ## Run maestro-flow skill tests only
	SKILLS_REPO_PATH=$(SKILLS_REPO_PATH) \
	  coder-eval run tasks/uipath-maestro-flow/*.yaml \
	  -e experiments/default.yaml -j 1

.DEFAULT_GOAL := help
