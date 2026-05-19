# Stub package fixtures — for process-running E2E tests

These `.zip` files are **packaged UiPath solutions** (Studio Web export, ready
for `uip solution publish`). `seed_process.py` publishes + deploys them in
`pre_run` for tests that need a process on the tenant.

| File | Used by | Notes |
|------|---------|-------|
| `e2e-stub-1.0.0.zip` | O2, O7, R6, R10, R11 (any test needing a process) | Quick stub; agent prints something and exits |
| `e2e-stub-1.0.1.zip` | O4 (process rollback target) | Same source, version bumped |
| `e2e-stub-long-1.0.0.zip` | O6 (jobs stop/restart) | Same workflow + ~30s delay so SoftStop has a window |

## How `seed_process.py` uses them

```yaml
# default — uses e2e-stub-1.0.0.zip
pre_run:
  - command: "TASK_ID=<slug> python3 .../seed_process.py"

# rollback target also published — uses both 1.0.0 and 1.0.1
pre_run:
  - command: "TASK_ID=<slug> SEED_PROCESS_TWO_VERSIONS=1 python3 .../seed_process.py"

# long-running variant — uses e2e-stub-long-1.0.0.zip
pre_run:
  - command: "TASK_ID=<slug> SEED_PROCESS_LONG=1 python3 .../seed_process.py"
```

After `pre_run`, `seed.json` contains `process_key`, `folder_path`,
`deployment_name`, `package_id`, `package_version`. The agent reads those.

`post_run` (`cleanup_platform_resources.py`) runs `uip solution deploy uninstall
<deployment_name>`, which removes the folder + process + any deployed resources.

## Rebuilding from source

`.zip` files are Studio Web exports — open the source solution in Studio Web,
click "Download" to get a `.zip`. To bump a version, edit the project's
`project.json` version field, re-download.

For the long variant, add a Delay activity (30s) at the top of `Main.xaml` and
re-export.

## Legacy: TRACES_SMOKE_PROCESS_KEY fallback

`seed_process.py` still honors the `TRACES_SMOKE_PROCESS_KEY` env var as a
fallback path (used by `traces_e2e.yaml` historically). If set, the env var
wins and these `.zip` fixtures are ignored.
