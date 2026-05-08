---
name: uipath-solution
description: "UiPath Solution lifecycle via the `uip solution` CLI — create solutions, add projects, refresh resource bindings, pack, publish, deploy with config, activate, manage. Use this BEFORE writing any code that talks to RCS or Studio Web's solution APIs."
when_to_use: "User wants to build, ship, or manage a multi-project UiPath solution: `solution new`, `solution project add`, `solution resource refresh`, `solution pack`, `solution publish`, `solution upload`, `solution deploy run`, `solution activate`, `solution uninstall`, `solution deploy config set/link/unlink`. Triggers: 'create a solution', 'add this project to my solution', 'refresh bindings', 'pack and deploy a solution', 'configure a deployment', 'set the value of a virtual asset before deploy', 'link to a cloud resource at deploy time'. NOT for individual Orchestrator resources outside a solution context (→uipath-resources, →uipath-orchestrator). NOT for Integration Service (→uipath-integration-service)."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Solution Lifecycle

Manage UiPath solutions end-to-end via the `uip solution` CLI: create, add projects, refresh resource declarations, pack, publish, upload to Studio Web, deploy with per-environment config, activate, and uninstall.

## Use the CLI. Don't roll your own REST.

**Always use `uip solution <verb>` commands**. Solutions involve RCS (Resource Catalog Service), Studio Web, deploy validation, virtual resource creation, and deploy-config link/unlink — all of which the CLI orchestrates correctly through `@uipath/resource-builder-sdk`. Do not call those services directly: the SDK enforces invariants (key stability, dedup, suffix uniqueness, virtual fallback) that you would get wrong by hand.

If you need to mutate a single field on a solution-level resource and there is no `solution resource update` command, see [scenarios/manual-edits.md](references/scenarios/manual-edits.md) for which fields are safe to hand-edit and which the SDK re-derives.

## When to Use This Skill

- **Concept overview** — solution vs project vs resource, lifecycle diagram, command tree → [solution.md](references/solution.md)
- **Author a solution** — `solution new`, `project add`, `resource refresh`, `resource list` → [develop-solution.md](references/develop-solution.md)
- **Pack, publish, deploy with config** — `pack`, `publish`/`upload`, `deploy run`, `deploy config set/link/unlink` → [pack-and-deploy.md](references/pack-and-deploy.md)
- **Activate and manage** — `solution activate`, `uninstall`, package management → [activate-and-manage.md](references/activate-and-manage.md)
- **Multi-project recipes / edge cases** (same-name resources, virtual assets, intra-solution refs, manual edits) → [scenarios.md](references/scenarios.md)

## Output Conventions

- Always pass `--output json` when scripting; the envelope is `{ Result, Code, Data, Pagination? }`.
- Action commands (refresh, pack, publish, deploy, activate) return PascalCase summaries (`Status`, `Created`, `Imported`, `Skipped`, etc.).
- `solution resource list --source local` returns the in-solution view (camelCase, full DTO); `--source remote` queries cloud.

## Cross-skill references

- Orchestrator admin (folders, jobs, machines, users) → [`uipath-orchestrator`](../uipath-orchestrator/SKILL.md)
- Resources outside a solution context (assets, queues, buckets, libraries, webhooks, triggers) → [`uipath-resources`](../uipath-resources/SKILL.md)
- Integration Service → [`uipath-integration-service`](../uipath-integration-service/SKILL.md)
- Login, global flags → [`uipath-cli`](../uipath-cli/SKILL.md)
