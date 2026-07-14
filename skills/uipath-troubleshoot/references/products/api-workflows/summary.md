# API Workflows Playbooks

Covers **why a UiPath API Workflow failed** — the JSON workflows run by `uip api-workflow run` and published to Orchestrator as API processes. Primary investigation surfaces: `uip api-workflow validate` / `run --no-auth` (local repro), `uip is connections ping` (connection health), and `uip or jobs get`/`logs`/`traces` + `uip traces spans get` (cloud runs).

**Overview:** [overview.md](./overview.md) — dependencies, evidence surfaces, fault families
**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — reproduce-locally-first, category order, connection verification, cloud-job correlation

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Run returns non-Successful status | Medium | Executor returns `Result: "Failure"` or the Orchestrator job faults: an activity threw, OR a `Response` deliberately set `markJobAsFailed: true`. Triage by category (Structure > Expression > Activity Config > Logic); reproduce with `run --no-auth`. | [run-not-successful.md](./playbooks/run-not-successful.md) |
| `<name> is not defined` at runtime | High | `ReferenceError` while `validate` still reports Valid. Loop iterator referenced without its `$` prefix (`currentItem` vs `$currentItem`), or an unwrapped string literal normalized to `${literal}` after a Studio Web save. | [expression-reference-error.md](./playbooks/expression-reference-error.md) |
| `$context.outputs.<Activity>` undefined | Medium | Silent wrong-result: producing activity missing its `export`, connector output read at the root instead of `.content`, slot-key-vs-export-bucket-key mismatch, or `$input.<name>` used instead of `$workflow.input.<name>`. | [output-undefined.md](./playbooks/output-undefined.md) |
| Connector call 401 in cloud | Medium | Runs locally, fails once published. Wrong activity kind for the endpoint (Http kind at a vendor connection), broken/expired connection, stale connection listing, or tenant/folder mismatch. The broken connection reads as `ConnectionNotEnabled` on `is connections ping`. | [connection-401.md](./playbooks/connection-401.md) |
| Pack / publish / deploy fails, or invisible in Studio Web | Medium | Wrong `Type`, publishing the `.nupkg` not the `.zip`, 401/403/409 on publish, stale generated descriptors, or a project scaffolded by hand without the `project.uiproj` + `Workflow.json` shape (deploys but won't open in Studio Web — authoring concern owned by `uipath-api-workflow`). | [publish-deploy-failure.md](./playbooks/publish-deploy-failure.md) |
