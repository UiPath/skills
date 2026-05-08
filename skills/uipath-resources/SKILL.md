---
name: uipath-resources
description: "UiPath Orchestrator resources via the `uip` CLI — assets, queues, queue items, storage buckets, bucket files, libraries, webhooks, triggers (time/queue/api). Use this BEFORE writing any custom Orchestrator REST API code for these resources."
when_to_use: "User wants to read or mutate any of: storage buckets and bucket files (upload/download/list/delete/share/presigned URLs), assets (text/integer/boolean/credentials), queues and queue items (create, add items, set progress, retry), libraries (.nupkg upload/download/list/versions), webhooks (create with events, update, ping, delete), triggers (time/cron, queue, api). Triggers: 'upload to bucket', 'create asset', 'add queue item', 'webhook for job.completed', 'cron trigger', 'list libraries', 'set up an API trigger', or any folder-scoped resource operation. NOT for jobs/processes/folders (→uipath-orchestrator). NOT for solution lifecycle (→uipath-solution). NOT for Integration Service (→uipath-integration-service)."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Orchestrator Resources

Manage Orchestrator-scoped resources via the `uip` CLI: storage buckets, assets, queues, libraries, webhooks, and triggers.

## Use the CLI. Don't roll your own REST.

**Always use `uip resource <subject> <verb>` commands**. Every resource in this skill is covered by a CLI subcommand — there is no resource here that requires hand-rolled HTTP calls.

If you find yourself thinking *"I'll grab the auth token and PUT to the bucket directly"* or *"I'll just call the OData endpoint myself"* — stop. Open the corresponding reference file in this skill, find the matching `uip resource ...` command, and use it. Reach for raw REST only after you have searched the references and `uip resource <subject> --help` and confirmed there is no command for what you need.

## When to Use This Skill

- **Storage buckets / files** — create buckets, upload/download files, generate presigned URLs → [work-with-storage.md](references/work-with-storage.md)
- **Assets** — text/integer/bool/credential, folder-scoped, with credential-store backing → [manage-assets.md](references/manage-assets.md)
- **Queues / queue items** — define queues, add items with `--reference` and `--specific-content`, retry, set progress → [process-queues.md](references/process-queues.md)
- **Triggers and webhooks** — schedule jobs (time/queue/api triggers), notify external systems on Orchestrator events → [triggers-and-webhooks.md](references/triggers-and-webhooks.md)
- **Resource tool overview + libraries** — `.nupkg` library upload/download/list → [resources.md](references/resources.md)

## Prerequisites

- Authenticated: `uip login` (see `uipath-platform` for auth flows).
- Tenant selected: `uip login tenant set <tenant-name>`.
- Folder context: most commands need `--folder-path "<name-or-path>"` or `--folder-key <guid>`. Buckets can also use `--all-folders`. Queues/triggers create derive folder from the release. Webhooks and libraries are tenant-scoped (no folder).

## Output Conventions

- Always pass `--output json` when scripting; the envelope is `{ Result, Code, Data, Pagination? }`.
- `resource-tool` returns the **full DTO** (camelCase) on list/get for assets, buckets, queues, queue items, libraries, webhooks. There is no `--all-fields` flag — what you see is the raw API shape.
- Action envelopes (Created/Updated/Deleted) use a small PascalCase shape: `{ Key, Name, Status }`.
- `triggers list` returns curated rows; `triggers get` returns the SDK DTO.

## Cross-skill references

- Folder management, processes (releases), jobs, machines, users → [`uipath-orchestrator`](../uipath-orchestrator/SKILL.md)
- Solution-level resource declarations (`bindings_v2.json`, `solution resource refresh`, virtual resources) → [`uipath-solution`](../uipath-solution/SKILL.md)
- IS connections / triggers (different system) → [`uipath-integration-service`](../uipath-integration-service/SKILL.md)
- Login, global flags, output formats → [`uipath-cli`](../uipath-cli/SKILL.md)
