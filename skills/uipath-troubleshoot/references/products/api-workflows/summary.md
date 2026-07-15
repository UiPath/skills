# API Workflows Playbooks

Covers **why a UiPath API Workflow failed** — the JSON workflows run by `uip api-workflow run` and published to Orchestrator as API processes. Primary investigation surfaces: `uip api-workflow validate` / `run --no-auth` (local repro), `uip is connections ping` (connection health), and `uip or jobs get`/`logs` + `uip traces spans get --job-key` (cloud runs).

**Overview:** [overview.md](./overview.md) — dependencies, evidence surfaces, fault families
**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — reproduce-locally-first, category order, connection verification, cloud-job correlation

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Run returns non-Successful status | Medium | Executor returns `Result: "Failure"` or the Orchestrator job faults: an activity threw, OR a `Response` deliberately set `markJobAsFailed: true`. Triage by category (Structure > Expression > Activity Config > Logic); reproduce with `run --no-auth`. | [run-not-successful.md](./playbooks/run-not-successful.md) |
| `<name> is not defined` at runtime | High | `ReferenceError` while `validate` still reports Valid. Loop iterator referenced without its `$` prefix (`currentItem` vs `$currentItem`), or an unwrapped string literal normalized to `${literal}` after a Studio Web save. | [expression-reference-error.md](./playbooks/expression-reference-error.md) |
| `$context.outputs.<Activity>` undefined | Medium | Producing activity missing its `export`, connector output read at the root instead of `.content`, slot-key-vs-export-bucket-key mismatch, or `$input.<name>` used instead of `$workflow.input.<name>`. Silent `undefined` on key mismatch; crashes `Cannot read properties of undefined` when `$context.outputs` doesn't exist at all. | [output-undefined.md](./playbooks/output-undefined.md) |
| Connector call 401/403 in cloud | Medium | Runs locally, fails once published. **401** (`Invalid Element token`): wrong activity kind (Http kind at a vendor connection), stale connection listing, or tenant/folder mismatch. **403 Forbidden**: broken/disabled or under-scoped connection — reads as `Result: "Failure"` / `not enabled` on `is connections ping`. | [connection-auth-failure.md](./playbooks/connection-auth-failure.md) |
| Pack / publish / deploy fails, or invisible in Studio Web | Medium | Wrong `Type`, publishing the `.nupkg` not the `.zip`, 401/403/409 on publish, stale generated descriptors, or a project scaffolded by hand without the `project.uiproj` + `Workflow.json` shape (deploys but won't open in Studio Web — authoring concern owned by `uipath-api-workflow`). | [publish-deploy-failure.md](./playbooks/publish-deploy-failure.md) |
