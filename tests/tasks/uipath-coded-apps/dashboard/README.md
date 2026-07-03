# Dashboard Capability — Test Suite

Coder-eval tasks for the `uipath-coded-apps` dashboard generation capability.
The skill builds production-ready React dashboards from natural-language prompts
using the `@uipath/uipath-typescript` SDK (compiler / metric-module architecture).

The shared validator `_shared/check_dashboard.py` auto-locates the generated
project (the skill scaffolds into a `<routingName>/` subdir) and checks the
compiler-model structure: `intent.json` (schemaVersion 2, no `fnBody`), metric
modules under `src/metrics/` exporting `fetchData`, generated widgets under
`src/dashboard/widgets/`, the `uipath.json` SDK config (read by the
`uipathCodedApps()` Vite plugin), and (with `--tsc`) a clean
`tsc --noEmit`.

## How to run

```bash
cd tests

# All dashboard tests (default experiment — dev/local, tempdir)
make test-uipath-coded-apps

# By tier
make tags TAGS="uipath-coded-apps smoke"        # PR-gate (fast)
make tags TAGS="uipath-coded-apps integration"  # Daily
make tags TAGS="uipath-coded-apps e2e"          # Nightly (full build + tsc gate)

# Single task (local harness with ANTHROPIC_API_KEY configured)
SKILLS_REPO_PATH=$(cd .. && pwd) .venv/bin/coder-eval run \
  tasks/uipath-coded-apps/dashboard/smoke/dashboard_plan_gate.yaml \
  -e experiments/default.yaml
```

## Layout

```
dashboard/
├── _shared/
│   └── check_dashboard.py  # Compiler-model structural + routing validator
├── smoke/                  # plan gate, plan-before-question, disambiguate (fast, no-build PR gate)
├── routing/                # agent/job classification trap
├── governance/             # gate open + gate closed (no-regression)
├── detail/                 # rowLink clickable
├── refuse/                 # impossible-literal → documented substitution
├── oauth/                  # post-approval client-ID passthrough (no re-ask, no self-provision)
├── semantic/               # Phase-3.5 compiles-green-wrong-rows fix loop
├── build/                  # scaffold (shape) + full e2e (real tsc gate)
└── deploy/                 # pack/publish/deploy command-sequence + governance target
```

Tier is a tag, not a folder. Full inline builds (build/, refuse/, routing/,
governance/, detail/, incremental/) are tagged `integration`/`e2e` and run
nightly at 200 turns. Only the fast, no-build gate tasks (smoke/) plus the
pre-seeded deploy command-shape check are tagged `smoke` for the 40-turn PR gate.

## Reports & artifacts (local runs mirror CI)

Every `coder-eval run` writes `tests/runs/<timestamp>/` with the exact structure CI uploads as its
artifact zip: `experiment.html` / `experiment.md` (run summary), and per task
`default/<task-id>/00/{task.html, task.json, task.log, artifacts/}` — `task.html` is the browser
report, `task.json` the machine-readable result + transcript, `artifacts/` the preserved sandbox
(node_modules pruned). Quick views:

```bash
.venv/Scripts/coder-eval report runs/<timestamp>   # scoreboard in the terminal (Scripts/ on Windows, bin/ on Linux)
start runs/<timestamp>/experiment.html             # full HTML report (Windows; use open/xdg-open elsewhere)
```

**Windows note:** the CLI lives at `.venv/Scripts/coder-eval.exe` (the Makefile assumes `.venv/bin`),
and `run_command`/heredoc `pre_run` criteria execute under cmd.exe locally — tasks in this suite use
`bash -c` wrappers + `_shared/seed_*.sh` so they run on both; `python3`-based criteria still need a
Linux run (or re-grade the preserved `artifacts/` manually with `_shared/check_dashboard.py`).

## Tenant cleanup

Build-path tasks create one real External Application per run (the skill's OAuth step) when the runner
is authenticated. Every such task runs `_shared/cleanup_external_apps.mjs` as its FIRST `post_run`:
it collects the clientId(s) the build wrote into the sandbox (`uipath.json`/`intent.json`), matches
them against `uip admin external-apps list`, and deletes only those — best-effort, always exit 0, so
cleanup never affects pass/fail.

Known residual leak (documented, no CLI delete verb exists): app packages uploaded by the deploy tasks'
`codedapp publish` calls.
