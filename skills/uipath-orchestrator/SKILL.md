---
name: uipath-orchestrator
description: "UiPath Orchestrator administration via the `uip or` CLI — folders, processes (releases), packages, jobs, machines, users, roles, sessions, calendars, credential stores, feeds, attachments, audit logs, settings. Use this BEFORE writing any custom Orchestrator REST API code for these resources."
when_to_use: "User wants to administer Orchestrator: create/list/move folders, list processes or upload packages, start a job, manage machines (templates, slots, assignment, sessions), import/edit/assign users and roles, configure tenant-level settings, browse audit logs, manage calendars or credential stores, list feeds, download attachments. Triggers: 'create folder', 'start a job', 'list processes', 'upload package', 'configure machine', 'add user to folder', 'list audit logs', 'create calendar', 'tenant settings'. NOT for assets, queues, queue items, buckets, libraries, webhooks, triggers (→uipath-resources). NOT for solution lifecycle or solution resource declarations (→uipath-solution). NOT for Integration Service (→uipath-integration-service)."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Orchestrator Administration

Manage Orchestrator infrastructure and workloads via the `uip or` CLI: folders, processes/releases, packages, jobs, machines, users, roles, sessions, calendars, credential stores, feeds, attachments, audit logs, settings.

## Use the CLI. Don't roll your own REST.

**Always use `uip or <subject> <verb>` commands**. Every Orchestrator surface in this skill is covered by a CLI subcommand. There is no admin operation here that requires hand-rolled HTTP calls.

If you find yourself thinking *"I'll just hit the OData endpoint myself"* — stop. Open the corresponding reference file, find the `uip or ...` command, and use it. Reach for raw REST only after you have searched the references and `uip or <subject> --help` and confirmed there is no command for what you need.

## When to Use This Skill

- **Set up a folder, users, roles, machines** → [setup-environment.md](references/setup-environment.md)
- **Upload packages, list processes, start/track jobs** → [run-jobs.md](references/run-jobs.md)
- **Tenant-level admin** — calendars, credential stores, settings, feeds, audit logs, attachments → [tenant-admin.md](references/tenant-admin.md)
- **Sessions** — toggle debug mode, list runtime sessions, set maintenance mode → [manage-sessions.md](references/manage-sessions.md)
- **Concept overview** — folders, runtimes, release vs package vs job → [orchestrator.md](references/orchestrator.md)

## Output Conventions

- Always pass `--output json` when scripting; the envelope is `{ Result, Code, Data, Pagination? }`.
- `orchestrator-tool` curates list/get output by default into a **PascalCase** projection of the most useful fields. Pass `--all-fields` on any list/get/versions/version-history command to get the **raw camelCase API DTO** instead.
- `audit-logs list` is the one intentional exception — every field on `AuditLogDto` is load-bearing for "who did what when", so it always returns the raw DTO and does not expose `--all-fields`.
- Action envelopes (Created/Updated/Deleted/Started/Stopped) use a small PascalCase shape: `{ Key, Name, Status }`.

## Cross-skill references

- Resources (assets, queues, buckets, libraries, webhooks, triggers) → [`uipath-resources`](../uipath-resources/SKILL.md)
- Solution lifecycle (pack/publish/deploy/activate) → [`uipath-solution`](../uipath-solution/SKILL.md)
- Integration Service (different system) → [`uipath-integration-service`](../uipath-integration-service/SKILL.md)
- Login, global flags, output formats → [`uipath-cli`](../uipath-cli/SKILL.md)
