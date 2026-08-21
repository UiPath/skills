---
name: uipath-insights
description: "UiPath Insights job monitoring via `uip insights` — query job execution metrics, failure analysis, and process performance. Covers job KPIs, failure reasons, completion trends, process breakdowns. Also filter discovery — folders, processes, queues, and machines with recent activity, for choosing exact scope before alerts or filtered queries. For Orchestrator job start/stop/logs→uipath-platform, root-cause analysis of specific errors→uipath-troubleshoot, RPA workflow authoring→uipath-rpa."
when_to_use: "User says 'job failures', 'automation health', 'job success rate', 'processing time', 'which processes fail the most', 'failure reasons', 'job trends', 'how many jobs ran', 'insights dashboard', 'job metrics', 'job KPIs', 'job performance', 'uncompleted jobs', 'pending jobs', 'faulted jobs', 'job timeline', 'process details', 'which folders can you see', 'what processes are active', 'find the folder key', 'discover queues', 'which machines reported', 'filter-folders', 'filter-processes'. Also 'uip insights', 'insights jobs'. NOT for starting/stopping jobs (uipath-platform), NOT for root-cause debugging of a specific job error (uipath-troubleshoot), NOT for queue item metrics (queue discovery is supported via filter-queues; metrics are not)."
allowed-tools: Bash, Read
---

# UiPath Insights

Use `uip insights` for job monitoring and monitoring-scope discovery. Read the guide for the task before running commands.

## When to Use This Skill

- Job health, success rate, failure count, or processing time across a tenant, folder, or process
- Job trends over time, or a comparison between two periods
- Which processes fail most, and which failure reasons recur
- Whether jobs are stuck, pending, or still running
- Finding the exact folder key, process name, queue name, or machine name to scope a query by

## Critical Rules

1. **Use `--output json`.** `jobs` commands return `{ Result, Code, Data }`. `filter-*` commands add `Pagination` and `Instructions`; quote those `Instructions` in the explanation. A failure envelope carries `Result`, `Message`, `Instructions`, `ErrorCode`, and `Retry`, with no `Code` and no `Data`. Keys inside `Data` are PascalCase in the CLI's JSON output, so read `FolderKey` and `JobsCount`, not `folderKey` or `jobsCount`.
2. **One subcommand per invocation, written literally.** Do not chain, loop, or parameterize `uip insights` commands: no `&&` or `;` chains, no `for` loops, and no shell variables holding the subcommand name or flag values. Resolve values such as epoch timestamps in a separate command first, then pass literal numbers. Never write `$(date ...)` or `$VAR` into a flag value.
3. **Use only the flags the guides document.** Identity, organization, and tenant come from the active session. Any tenant flag you find is deprecated and is rejected outright on `filter-*` commands, so do not use one. If a filter is not in the guide's shared-options list, it does not exist.
4. **Every `jobs` command needs a time range.** Pass `--time-range <minutes>` (60 = 1h, 1440 = 24h, 10080 = 7d, 43200 = 30d), or both `--started-after` and `--started-before`. Omitting both is rejected locally and exits 1. `filter-*` commands take no time flags.
5. **Start with `summary`, then drill down.** After any scope discovery the task needs, begin a job investigation with `uip insights jobs summary` for the totals, then run the targeted subcommands. The summary supplies the denominator that makes a failure count meaningful.
6. **Treat empty data as bounded evidence.** Empty results can reflect the chosen time window, the recent-activity window, caller visibility, or tenant provisioning. They do not prove that a resource or event never existed.
7. **Use the CLI instead of raw Insights APIs.** It owns authentication, tenant routing, validation, and error handling.
8. **Do not retry automatically.** Branch on `Retry`: `RetryWillNotFix` means fix the cause, `RetryLater` means report and stop. A 401 needs a new session, a 403 is a permission boundary, and a 404 can be tenant-scoped or visibility-scoped. Each guide documents the error shapes for its own commands.
9. **Never run `uip login` yourself.** It opens an interactive browser flow that will hang the session. Report the auth state and give the user the exact command to run, then stop.
10. **Discover identifiers instead of guessing.** Use [`references/filter-discovery-guide.md`](references/filter-discovery-guide.md) to resolve monitoring scope. Page through all results before concluding a resource is absent.
11. **Hand off causal debugging.** Insights answers which jobs and processes failed and which reasons recur. It does not explain one job's exception or how to fix it. Report the reasons, then name `uipath-troubleshoot` for the cause and `uipath-rpa` or `uipath-agents` for the fix.

## Shared Workflow

1. Check the active login when the task will call UiPath Cloud:

   ```bash
   uip login status --output json
   ```

2. Read the guide the Task Navigation table below names for this task.
3. Run the subcommand and parse `Data` for the result. On `filter-*` commands also read `Pagination` for list completeness.

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

Read only the guides the task needs. A job investigation that must first resolve a folder, process, or machine needs the filter guide, then the jobs guide.

## Scope Boundaries

`uip insights` ships two command families: `jobs` and `filter-folders` / `filter-processes` / `filter-queues` / `filter-machines`. If a request needs anything else, say it is not available rather than guessing a subcommand.

| Request | Route |
|---|---|
| Start, stop, restart, or inspect logs for an individual Orchestrator job | `uipath-platform` |
| Diagnose the root cause of a specific job error | `uipath-troubleshoot` |
| Fix the workflow or agent that caused a failure | `uipath-rpa` or `uipath-agents` |
| Query queue item metrics | Not supported; `filter-queues` discovers queue scope only |
| Alert definitions, dashboards, or robot utilization | Not in the shipped `uip insights` surface |

## Anti-patterns

- Do not add `--limit` or `--offset` to a `jobs` command. Only `filter-*` commands page.
- Do not reuse an identifier from an example. Folder keys, process names, and machine names come from a `filter-*` result or from the user.

## Completion Output

Close with the answer, the window queried, the active organization and tenant, and the filters applied. For `filter-*` results, say whether every page was retrieved. For permission-limited or empty results, state what the result does and does not prove.
