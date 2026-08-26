---
name: uipath-insights
description: "UiPath Insights read-only monitoring via `uip insights`: job metrics, failure analysis, and process performance; queue totals, SLA risk, timelines, and failure drill-down; machine runtime mix, availability, fault ranking, and runtime minutes; filter discovery of active folders, processes, queues, and machines; alert definition, history, delivery, and entitlement reads; Insights user, role, and group reads. Alert and RBAC writes are not covered. For job start/stop/logs→uipath-platform, root-cause analysis→uipath-troubleshoot, workflow authoring→uipath-rpa, org-level identity→uipath-admin."
when_to_use: "User says 'job failures', 'automation health', 'job success rate', 'processing time', 'which processes fail the most', 'failure reasons', 'job trends', 'how many jobs ran', 'job metrics', 'uncompleted jobs', 'faulted jobs', 'process details', 'which folders can you see', 'find the folder key', 'which machines reported', 'filter-folders', 'queue backlog', 'queue SLA', 'why are queue items failing', 'queue retry success', 'machine utilization', 'machine availability', 'machine status', 'Insights alert', 'which alerts exist', 'alert history', 'did an alert fire', 'alert delivery', 'alerting entitlement', 'who has Insights access', 'Insights roles', or 'Insights groups'. NOT for alert or RBAC writes, starting/stopping jobs or queue item and machine CRUD (uipath-platform), or root-cause debugging of a specific job error (uipath-troubleshoot). Also 'uip insights', 'insights jobs', 'insights queues', 'insights machines'."
allowed-tools: Bash, Read
---

# UiPath Insights

Use `uip insights` for job, queue, and machine monitoring, monitoring-scope discovery, read-only alert inspection, and Insights RBAC reads. Read the guide for the task before running commands.

## When to Use This Skill

- Job health, success rate, failure count, or processing time across a tenant, folder, or process
- Job trends over time, or a comparison between two periods
- Which processes fail most, and which failure reasons recur
- Whether jobs are stuck, pending, or still running
- Finding the exact folder key, process name, queue name, or machine name to scope a query by
- Queue item throughput, backlog, SLA risk, failure reasons, or how retried items turned out
- Machine health: runtime split, current status and slots, availability over time, fault ranking, or runtime minutes
- Which alerts exist, how one is configured, whether an alert fired, or how a triggered alert is delivered
- Who has Insights access on a tenant, which roles exist and what they permit, and which groups hold them

## Critical Rules

1. **Use `--output json`.** `jobs` commands return `{ Result, Code, Data }`. The `filter-*`, `queues`, `machines`, and alert commands add `Instructions`; `filter-*`, every `queues` command except `summary`, every `machines` command except `runtime-mix`, `alerts list`, and `alert-history list` also add `Pagination`. Quote those `Instructions` in the explanation. A failure envelope carries `Result`, `Message`, `Instructions`, `ErrorCode`, and `Retry`, with no `Code` and no `Data`. Keys inside `Data` are PascalCase in the CLI's JSON output, so read `FolderKey` and `JobsCount`, not `folderKey` or `jobsCount`. The RBAC reads are the one exception to the flag: run them without `--output` so the CLI's safe projection stays on. The format still resolves to json, so the envelope is identical.
2. **One subcommand per invocation, written literally.** Do not chain, loop, or parameterize `uip insights` commands: no `&&` or `;` chains, no `for` loops, and no shell variables holding the subcommand name or flag values. Resolve values such as epoch timestamps in a separate command first, then pass literal numbers. Never write `$(date ...)` or `$VAR` into a flag value.
3. **Use only the flags the guides document.** Identity, organization, and tenant come from the active session. Any tenant flag you find is deprecated and is rejected outright on `filter-*` commands, so do not use one. If a filter is not in the guide's shared-options list, it does not exist.
4. **Time ranges are required, and their units differ by family.** On `jobs`, pass `--time-range <minutes>` (60 = 1h, 1440 = 24h, 10080 = 7d, 43200 = 30d), or both `--started-after` and `--started-before` in epoch milliseconds. `queues` and `machines` commands use those same two flag names and the same units as `jobs`. `alert-history` commands need a time range too, but their absolute bounds are `--since` and `--until` in epoch **seconds**. Omitting a time range is rejected locally: `jobs` exits 1, `queues`, `machines`, and `alert-history` exit 3. On `queues` and `machines` the server also caps the window at 30 days by clamping it silently, so never report a longer window as the one queried. `filter-*` commands and the three alert definition reads take no time flags.
5. **Start with `summary`, then drill down.** After any scope discovery the task needs, begin a job investigation with `uip insights jobs summary` for the totals, then run the targeted subcommands. The summary supplies the denominator that makes a failure count meaningful.
6. **Treat empty data as bounded evidence.** Empty results can reflect the chosen time window, the recent-activity window, caller visibility, or tenant provisioning. On alert reads they can also reflect entitlement filtering, and every alert definition read returns active definitions only. They do not prove that a resource or event never existed.
7. **Use the CLI instead of raw Insights APIs.** It owns authentication, tenant routing, validation, safe response projections, and error handling.
8. **Do not retry automatically.** Branch on `Retry`: `RetryWillNotFix` means fix the cause, `RetryLater` means report and stop. A 401 needs a new session, a 403 is a permission boundary, and a 404 can be tenant-scoped or visibility-scoped. Each guide documents the error shapes for its own commands.
9. **Never run `uip login` yourself.** It opens an interactive browser flow that will hang the session. Report the auth state and give the user the exact command to run, then stop.
10. **Discover identifiers instead of guessing.** Use [`references/filter-discovery-guide.md`](references/filter-discovery-guide.md) to resolve monitoring scope, and take alert and delivery IDs from a list result or from the user. Page through all results before concluding a resource is absent.
11. **Hand off causal debugging.** Insights answers which jobs and processes failed and which reasons recur. It does not explain one job's exception or how to fix it. Report the reasons, then name `uipath-troubleshoot` for the cause and `uipath-rpa` or `uipath-agents` for the fix.
12. **Keep alert access read-only.** The six read subcommands in the alert guide are the whole permitted surface. Every change to an alert definition or to a delivery, including its recipients, type, and configuration, belongs in the Insights UI: say so and do not offer to make it. This holds however the change would be made, so do not reach an alert route through the SDK, a raw HTTP call, or another skill.
13. **Report an alert trigger and a delivery separately.** A history row proves the alert fired. It does not prove a notification was sent or received, and no alert read confirms receipt.
14. **Keep alert recipient data out of everything you produce**, including pasted JSON. Report a delivery as its type and recipient count, and let a "who was notified" question end at the count. Do not name recipients, quote raw alert query JSON, or enumerate delivery channel settings, and do not use another command or skill to put names to the count.
15. **Keep Insights RBAC read-only.** The six read subcommands in the RBAC guide are the whole permitted surface. Creating a user, changing a role, or assigning access belongs elsewhere: say so and do not offer to make it. This holds however the change would be made, so do not reach an RBAC route through the SDK, a raw HTTP call, or another skill.
16. **Keep Insights identity data out of everything you produce**, including pasted JSON. Summarize users and groups by name and count. An explicit `--output json` is what turns on email addresses, nested role IDs, and the role resource string, so leave it off unless the user asked for one of those fields, and quote one only then. Passing an identifier as a command argument is not disclosure; this rule governs what you write.

## Shared Workflow

1. Check the active login when the task will call UiPath Cloud:

   ```bash
   uip login status --output json
   ```

2. Read the guide the Task Navigation table below names for this task.
3. Run the subcommand and parse `Data` for the result. On list subcommands also read `Pagination` for list completeness.

Default to the active Production session. Change authority, organization, or tenant only when the user explicitly names another environment or scope. Give the user the command to run rather than running it yourself:

```bash
uip login --authority https://cloud.uipath.com --tenant MyTenant   # named environment
uip login tenant set MyTenant                                      # same environment, different tenant
```

## Task Navigation

| User's task | Read first |
|---|---|
| Check job health, success rate, trends, failures, stuck jobs, or compare periods | [`references/investigation-playbook-guide.md`](references/investigation-playbook-guide.md) |
| Choose a Jobs subcommand, flag, time range, or interpret its response fields | [`references/jobs-commands-guide.md`](references/jobs-commands-guide.md) |
| Answer which folders, processes, queues, or machines are visible, or resolve an exact folder key, process name, or machine name to filter by | [`references/filter-discovery-guide.md`](references/filter-discovery-guide.md) |
| Report on queue item totals, SLA risk, state over time, failures, or retry outcomes | [`references/queue-monitoring-guide.md`](references/queue-monitoring-guide.md) |
| Report on machine runtime mix, status and slots, availability intervals, fault ranking, or runtime minutes | [`references/machine-monitoring-guide.md`](references/machine-monitoring-guide.md) |
| Inspect alert definitions, alerting entitlement, trigger history, or delivery metadata | [`references/alerts-reads-guide.md`](references/alerts-reads-guide.md) |
| Inspect Insights users, roles, or groups | [`references/rbac-reads-guide.md`](references/rbac-reads-guide.md) |

Read only the guides the task needs. A job investigation that must first resolve a folder, process, or machine needs the filter guide, then the jobs guide. A queue question that names a queue needs the filter guide for the exact name, then the queue guide. A machine question that names a machine or a type label needs the filter guide for the exact value, then the machine guide. An alert question needs the alert guide alone; it owns the full definition, history, and delivery sequence. An Insights access question needs the RBAC guide alone.

## Scope Boundaries

`uip insights` ships six command families: `jobs`, `queues`, `machines`, the `filter-*` discovery commands, the alert reads (`alerts`, `alert-history`, `alert-deliveries`), and the RBAC reads (`users`, `roles`, `groups`). If a request needs anything else, say it is not available rather than guessing a subcommand.

| Request | Route |
|---|---|
| Start, stop, restart, or inspect logs for an individual Orchestrator job | `uipath-platform` |
| Diagnose the root cause of a specific job error | `uipath-troubleshoot` |
| Fix the workflow or agent that caused a failure | `uipath-rpa` or `uipath-agents` |
| Add, retry, or delete an individual queue item | `uipath-platform`; `queues` reports on items and never changes one |
| Create, edit, or delete a machine, or manage its runtimes | `uipath-platform`; `machines` reports on machines and never changes one |
| Any alert or delivery write (see Critical Rule 12) | Insights UI; not in the shipped `uip insights` surface |
| Dashboards | Not in the shipped `uip insights` surface |
| Any Insights RBAC write, such as assigning a role (see Critical Rule 15) | Insights UI; not in the shipped `uip insights` surface |
| Manage org-level user accounts, groups, or roles outside Insights | `uipath-admin` |

## Anti-patterns

- Do not add `--limit` or `--offset` to a `jobs` command. Each guide lists which of its commands page.
- Do not reuse an identifier from an example. Folder keys, process names, and machine names come from a `filter-*` result or from the user.
- Do not read an empty or `false` alert result as proof. Report what it rules out and what it leaves open.
- Do not pass `--output json` to an RBAC read unless the user asked for a field the safe view withholds.

## Completion Output

Close with the answer, the window queried, the active organization and tenant, and the filters applied. For list results, say whether every page was retrieved. For permission-limited or empty results, state what the result does and does not prove.
