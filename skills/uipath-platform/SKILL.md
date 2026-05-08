---
name: uipath-platform
description: "Router skill for UiPath — load this when you're unsure which focused skill covers a task. Points at uipath-cli, uipath-orchestrator, uipath-resources, uipath-solution, uipath-integration-service. Use BEFORE writing any custom code that calls UiPath APIs."
when_to_use: "User mentions UiPath, Orchestrator, Studio Web, agent / process / workflow / package / asset / queue / bucket / library / webhook / trigger / connector / connection / activity / solution / pack / publish / deploy, but the more specific skill (resources, orchestrator, solution, integration-service, cli) hasn't been loaded yet. Stop reading after the routing table — pick a focused skill and load it."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Platform — Router

The UiPath CLI surface is large enough that it lives in **focused skills**, not in this one. This skill is a router: it tells you which skill to load for the task at hand, and reminds you to use `uip` CLI commands instead of hand-rolled REST.

## Use the CLI. Don't roll your own REST.

**Always use `uip` CLI commands.** The CLI covers Orchestrator, Studio Web/RCS, Integration Service, and solution lifecycle end-to-end. Hand-rolling HTTP calls (e.g. building auth headers from `~/.uipath/.auth` and POSTing to `/odata/...`) almost always misses something the CLI gets right (folder header, OData filter shape, retry semantics, validation envelopes). Reach for raw REST only after you have searched the focused skill below for your task and confirmed there is no `uip` command for what you need.

## Where do I go?

| You want to... | Load skill |
|---|---|
| Log in / log out / switch tenant / set output format / find a command by keyword | [`uipath-cli`](../uipath-cli/SKILL.md) |
| Create folders, manage users/roles/machines, start jobs, upload packages, manage processes (releases), tenant-level admin (calendars, credential stores, audit logs, settings, feeds, attachments, sessions) | [`uipath-orchestrator`](../uipath-orchestrator/SKILL.md) |
| Manage Orchestrator-scoped resources: storage buckets and bucket files, assets, queues and queue items, libraries (.nupkg), webhooks, triggers (time/queue/api) | [`uipath-resources`](../uipath-resources/SKILL.md) |
| Build, pack, publish, deploy, activate, or maintain a multi-project UiPath **solution** | [`uipath-solution`](../uipath-solution/SKILL.md) |
| Integration Service — connectors, connections, activities, IS triggers, agent-workflow reference resolution | [`uipath-integration-service`](../uipath-integration-service/SKILL.md) |
| Author UiPath workflows themselves (`.cs` coded or `.xaml`) | [`uipath-rpa`](../uipath-rpa/SKILL.md) |
| Test Manager (test projects, cases, sets, executions, reports) | [`uipath-test`](../uipath-test/SKILL.md) |
| Agents (Python agent projects, prompts, tools, memory) | [`uipath-agents`](../uipath-agents/SKILL.md) |

## Common pitfalls before you load a focused skill

1. **Folder context.** Most resource and orchestrator commands need either `--folder-path "<name-or-path>"` or `--folder-key <guid>`. A few commands are tenant-scoped (libraries, webhooks, calendars, credential stores, settings, audit logs). The error message tells you which.
2. **Output is JSON-first.** Always pass `--output json` when scripting. The envelope is `{ Result, Code, Data, Pagination? }` for success or `{ Result: "Failure"|"ValidationError", Message, Instructions }` for failure. Exit code is non-zero on failure.
3. **Curated vs raw output.** `orchestrator-tool` curates list/get output by default into a PascalCase projection; `--all-fields` returns the raw camelCase DTO. `resource-tool` always returns the raw DTO (no curation, no `--all-fields` flag). Don't mix them up when parsing.
4. **PascalCase keys are convention for UiPath envelopes.** `Result`, `Code`, `Data`, `Pagination`, `Returned`, `Limit`, `Offset`, `HasMore`. Keys *inside* `Data` follow the rule above (curated PascalCase or raw camelCase).

That's enough to get oriented. **Pick the skill row from the table that matches your task and load it now** — don't try to do real work from this router.
