# DevOps Readiness Checklist

Source control, CI/CD, and deployment governance checks. Applies to ALL project types (RPA, agents, flows, coded apps).

## Source Control Hygiene

| Check | Severity | How to Verify |
|---|---|---|
| Repository under version control (Git, Azure Repos, etc.) | Warning | `git rev-parse --is-inside-work-tree` should succeed |
| `.gitignore` present at project / solution root | Warning | `ls .gitignore` |
| `.gitignore` excludes Studio runtime artifacts: `.local/`, `.codedworkflows/`, `.objects/` (Object Repository binary cache), `.tmh/`, `.entities/` runtime dirs | Warning | Read `.gitignore` and verify these patterns are present |
| `.gitignore` excludes `.nupkg` package artifacts and `bin/` / `obj/` build outputs | Warning | Verify exclusions |
| `.gitignore` excludes `.env` files, credential files (`*.pfx`, `*.key`, `credentials.json`) | Critical | Verify exclusions; cross-check no such files in `git ls-files` |
| `.gitignore` excludes IDE/OS noise (`.DS_Store`, `Thumbs.db`, `*.user`, `.vs/`) | Info | Verify exclusions |
| No binary files committed (Excel data files, screenshots beyond informative ones, large media) | Warning | `git ls-files | xargs -I {} stat -c "%s {}" {} | sort -rn | head` — flag large binaries |
| No secrets in commit history | Critical | Use a secret scanner (`trufflehog`, `gitleaks`) on the repo. Even one historical commit with a secret = compromised credential, must rotate |
| Agent prompts (`agent.json`, system prompts) are version-controlled (not stored only in Studio Web UI) | Warning | For agent projects, `agent.json` should be in the repo with the rest of the source |

## Branching and Code Review

| Check | Severity | How to Verify |
|---|---|---|
| Long-lived branches per environment OR trunk-based with environment configuration | Info | Check branch structure |
| Pull requests required before merge to main / production branches | Warning | Check repo settings for branch protection rules |
| Code review approval required for production-bound changes | Warning | Check PR policy |
| CI runs on PRs (validation, tests, Workflow Analyzer) | Warning | Check CI config (`.github/workflows/`, `azure-pipelines.yml`, etc.) |

## CI/CD Pipeline

| Check | Severity | How to Verify |
|---|---|---|
| Automated build pipeline exists | Warning | Check for CI config files |
| Pipeline runs validation (`uip rpa get-errors` / `uip flow validate` / `uip agent validate`) on every commit | Warning | Inspect pipeline steps |
| Pipeline runs Workflow Analyzer with project's analyzer rule set, fails on Error-level violations | Warning | Inspect pipeline; check for analyzer step |
| Pipeline runs unit / smoke tests | Warning | Inspect pipeline test step |
| Pipeline publishes packages to a feed (not manual Studio publish) | Critical | Check pipeline; verify production publishes go through pipeline only |
| Pipeline supports environment promotion (Dev → Test → UAT → Prod) with separate package versions or environment-specific deployment | Warning | Check pipeline structure |
| Pipeline failure blocks production deployment | Critical | Check pipeline gates |

## Configuration Separation

| Check | Severity | How to Verify |
|---|---|---|
| Per-environment configs are NOT all committed in plaintext to the same branch (use environment-specific assets, not duplicated config files in the repo) | Warning | Check for `config.dev.json` / `config.prod.json` containing environment-specific URLs / IDs / tokens — these belong in Orchestrator assets per environment |
| Environment names (dev / test / prod) NOT hardcoded in source — environment is determined by the Orchestrator folder the bot runs in | Warning | Grep source for `"prod"` / `"production"` / `"dev"` hardcoded strings outside config / environment-aware logic |
| Secrets pulled from Orchestrator Credential assets / external vault at runtime, not embedded in config files | Critical | Verify no plaintext credentials in any committed file |

## Governance Alignment for Agents and Maestro

| Check | Severity | How to Verify |
|---|---|---|
| Agent prompts changes go through PR review (same governance as RPA code) | Warning | Check whether `agent.json` modifications are reviewed before merge |
| Agent evaluation runs in CI; deployment blocked if eval score regresses below threshold | Warning | Check pipeline for eval execution + threshold gate |
| Maestro `.bpmn` / `.flow` changes go through PR review | Warning | Verify orchestration files are not edited directly in the Maestro UI on production |
| Production agent deployments require approval (manual gate in pipeline OR separate approval workflow) | Warning | Check pipeline / Orchestrator approval policy for AI-bearing artifacts |
