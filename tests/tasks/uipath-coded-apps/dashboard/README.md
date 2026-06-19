# Dashboard Capability — Test Suite

Coder-eval tasks for the `uipath-coded-apps` dashboard generation capability.
The skill builds production-ready React dashboards from natural-language prompts
using the `@uipath/uipath-typescript` SDK (compiler / metric-module architecture).

The shared validator `_shared/check_dashboard.py` auto-locates the generated
project (the skill scaffolds into a `<routingName>/` subdir) and checks the
compiler-model structure: `intent.json` (schemaVersion 2, no `fnBody`), metric
modules under `src/metrics/` exporting `fetchData`, generated widgets under
`src/dashboard/widgets/`, the OAuth-PKCE env vars, and (with `--tsc`) a clean
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
├── TEST_PLAN.md            # Suite reference (start here)
├── _shared/
│   └── check_dashboard.py  # Compiler-model structural + routing validator
├── smoke/                  # plan gate, plan-before-question, disambiguate, metric-modules, scaffold
├── routing/                # agent/job classification trap
├── governance/             # gate open + gate closed (no-regression)
├── detail/                 # rowLink clickable
├── build/                  # full e2e (real tsc gate)
└── deploy/                 # pack/publish/deploy command-sequence
```
