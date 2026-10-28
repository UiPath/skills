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
uip solution resources refresh --output json             # from /solution
uip solution publish --output json                       # from /solution; lists destinations when several exist
uip solution publish --location "<key or name>" --output json
uip solution publish --personal-workspace --output json
```

Run `resources refresh` first (Rule 15): it syncs artefact files and debug overwrites from `bindings_v2.json` before Studio Web packages them. Studio Web intercepts `solution publish` and packages the open solution itself, so do not run `maestro case pack` or `solution pack` (`solution pack` is not in the Studio Web CLI). Run `publish` with no destination flag first — with one destination it publishes there; with several it publishes nothing and prints the list, so ask the user which to use and rerun with `--location` (or `--personal-workspace`). Publish is asynchronous: report the destination, version, and request id, and verify the terminal state in Studio Web's Publish history.
<!--skill-flavor:phase-seven-commands:end-->

<!--skill-flavor:phase-seven-on-failure:start-->
If `publish` fails, print the CLI error verbatim, note it in `build-issues.md`, and re-show the Phase 7 prompt. An unknown-destination error lists the valid destinations — pick from that list rather than guessing. A `processKey` collision means the `name+version` pair already exists on the feed — re-run with a bumped `--version`.
<!--skill-flavor:phase-seven-on-failure:end-->

<!--skill-flavor:phase-seven-next-steps:start-->
Before the prompt: `Suggested next steps: publish to Orchestrator when you want the case on the tenant solution feed, or stop here if Studio Web and debug are enough.` After a successful publish: `Suggested next steps: check the publish result in Studio Web's Publish history, then deploy it to an Orchestrator folder from Orchestrator.` On `Done`: `Suggested next steps: review the case plan in Studio Web, or update sdd.md and re-run when you want changes.`
<!--skill-flavor:phase-seven-next-steps:end-->

<!--skill-flavor:phase-table-six-row:start-->
| **6 — Debug** | Optional debug run the user starts from the Case Designer (real execution — emails, API calls, etc.); the agent runs no debug command | The outcome the user reports | `Debug in the Case Designer` / `Continue to publish`; a re-publish after a fix is confirmed separately |
<!--skill-flavor:phase-table-six-row:end-->

<!--skill-flavor:phase-six-run-option:start-->
- `Debug in the Case Designer` — `uip maestro case debug` is not in the Studio Web CLI. Tell the user to start the run from the Case Designer's Debug control and share the outcome; record a failure they report verbatim in `build-issues.md`.
<!--skill-flavor:phase-six-run-option:end-->

<!--skill-flavor:phase-six-requirements:start-->
The run happens in the open Studio Web solution, started by the user; nothing here uploads or runs it.
<!--skill-flavor:phase-six-requirements:end-->
