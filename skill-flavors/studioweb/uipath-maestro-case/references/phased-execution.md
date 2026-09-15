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
Before the prompt: `Suggested next steps: publish to Orchestrator when you want the case on the tenant solution feed, or stop here if Studio Web and debug are enough.` After a successful publish: `Suggested next steps: check the publish result in Studio Web's Publish history, then deploy it to an Orchestrator folder from Orchestrator.` On `Done`: `Suggested next steps: review caseplan.json in Studio Web, or update sdd.md and re-run when you want changes.`
<!--skill-flavor:phase-seven-next-steps:end-->
