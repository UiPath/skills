<!--skill-flavor:structural-scaffolding:start-->
- Project scaffolding (`uip maestro case init "<ProjectName>"` from `/solution`, plus JSON scaffolding from `plugins/case/impl-json.md`); the open Studio Web solution is the only solution.
<!--skill-flavor:structural-scaffolding:end-->

<!--skill-flavor:phase-table-seven-row:start-->
| **7 — Publish to Orchestrator** | Optional `solution publish` of the open solution to the tenant solution feed (Studio Web owns packaging) | publish result printed | `Publish to Orchestrator` / `Done` |
<!--skill-flavor:phase-table-seven-row:end-->

<!--skill-flavor:phase-seven-commands:start-->
Auth is injected by the host — no `uip login`.

### Publish commands

```bash
uip solution publish --output json                       # from /solution; lists destinations when several exist
uip solution publish --location "<key or name>" --output json
uip solution publish --personal-workspace --output json
```

Studio Web intercepts `solution publish` and packages the open solution itself: `resources refresh`, `maestro case pack`, and `solution pack` are Node-CLI-only and are not run in Studio Web. Run with no destination flag first — with one destination it publishes there; with several it publishes nothing and prints the list, so ask the user which to use and rerun with `--location` (or `--personal-workspace`). Publish is asynchronous: report the destination, version, and request id, and verify the terminal state in Studio Web's Publish history.
<!--skill-flavor:phase-seven-commands:end-->

<!--skill-flavor:phase-seven-on-failure:start-->
If `publish` fails, print the CLI error verbatim, note it in `build-issues.md`, and re-show the Phase 7 prompt. An unknown-destination error lists the valid destinations — pick from that list rather than guessing. A `processKey` collision means the `name+version` pair already exists on the feed — re-run with a bumped `--version`.
<!--skill-flavor:phase-seven-on-failure:end-->

<!--skill-flavor:phase-seven-next-steps:start-->
Before the prompt: `Suggested next steps: publish to Orchestrator when you want the case on the tenant solution feed, or stop here if Studio Web and debug are enough.` After a successful publish: `Suggested next steps: check the publish result in Studio Web's Publish history, then deploy it to an Orchestrator folder from Orchestrator.` On `Done`: `Suggested next steps: review the case plan in Studio Web, or update sdd.md and re-run when you want changes.`
<!--skill-flavor:phase-seven-next-steps:end-->

<!--skill-flavor:phase-table-six-row:start-->
| **6 — Debug** | Optional debug run through the host (real execution: emails, API calls, etc.) | Run status, logs, and trace printed | `Run debug session` / `Continue to publish`; a re-publish after a fix is confirmed separately |
<!--skill-flavor:phase-table-six-row:end-->

<!--skill-flavor:phase-six-run-option:start-->
- `Run debug session`: run `uip maestro case debug "<ProjectName>"`. It waits for a terminal state.
<!--skill-flavor:phase-six-run-option:end-->

<!--skill-flavor:phase-six-requirements:start-->
The host runs the project saved in the open solution: no login, upload, or project path. Output is plain text: status, `Trace ID`, run logs, execution trace. Exit 1 means the run faulted.
<!--skill-flavor:phase-six-requirements:end-->

<!--skill-flavor:phase-six-refresh-note:start-->
- Run no `uip solution resources refresh` before debug; the host keeps solution resources in sync.
<!--skill-flavor:phase-six-refresh-note:end-->
