# Stub solution package

`e2e-stub-1.0.0.zip` — pre-built minimal UiPath coded Python agent. Used by
`uipath-solution/operate/deploy_round_trip_e2e` (the test publishes + deploys
it as part of the scenario) and `config_lifecycle_e2e` (config edits against
its config file).

## Tenant setup for job-running tests

The job-starting tests (`job_run_logs`, `job_control`, `trigger_time`,
`webhook_signed`, `package_download`) read `E2E_PROCESS_KEY` and
`E2E_LONG_PROCESS_KEY` env vars. Those keys must reference live processes on
the tenant. The follow-up PR ships the long-running and 1.0.1 stub variants
needed for the full provisioning recipe.

For one-time admin setup on a fresh tenant (e.g. CI's `alpha codereval/
DefaultTenant`):

```bash
# Publish + create the short process directly (bypasses Solution Pipeline)
unzip -o e2e-stub-1.0.0.zip -d /tmp/short
uip or packages upload /tmp/short/files/*/e2e-stub*.nupkg
uip or processes create --folder-path Shared --name e2e-stub-short \
  --package-key e2e-stub.process.e2e-stub --package-version 1.0.0

# Assign a Serverless machine to Shared so jobs actually execute
SERVERLESS=$(uip or machines list --output json \
  | jq -r '.Data[]|select(.Scope=="Serverless" and (.Name|test("[Dd]efault")))|.Key' | head -1)
uip or machines assign "$SERVERLESS" --folder-path Shared
```

Take the key from `uip or processes list --folder-path Shared --output json`
and export as `E2E_PROCESS_KEY` (or set as CI secret —
`tests/experiments/nightly.yaml` forwards it through the docker sandbox).

`E2E_LONG_PROCESS_KEY` follows the same recipe with the long-running stub
variant shipped in the follow-up PR.

## Rebuilding from source

`.zip` files are Studio Web exports — open the source solution in Studio Web,
click "Download" to get a `.zip`. To bump a version, edit the project's
`project.json` version field, re-download.
