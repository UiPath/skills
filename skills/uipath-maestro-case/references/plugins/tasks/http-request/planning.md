# http-request task — Planning

One HTTP call inside a stage, sent directly or with a connector's connection for authentication. Built-in type: the request is stated in the SDD, nothing is resolved from the registry.

## When to Use

Pick this plugin when the sdd.md labels a task `http-request`: a single request whose method, URL, headers, query and body the SDD states.

Distinguish from:

- **A curated connector operation** (Create Issue, Send Message) → [connector-activity](../connector-activity/planning.md). Prefer it whenever one exists for the call.
- **More than one call, or logic between calls** → [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

The task block states the request as these lines:

| Line | Required | Notes |
|---|---|---|
| `**Method:**` | Yes | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS` or `HEAD`. A missing or other method is reported in `Data.Unresolved[]`. |
| `**URL:**` | Yes | Absolute URL, or a path relative to the connector's base URL in connector mode. |
| `**Headers:**` | No | One JSON object in backticks. Anything else is reported in `Data.Unresolved[]`. |
| `**Query:**` | No | One JSON object in backticks. |
| `**Body:**` | No | A JSON literal in backticks, or an `=` expression. Anything else is reported in `Data.Unresolved[]`. |
| `**Connector Key:**` | No | Connector mode: reuse that connector's authentication. |
| `**Connection ID:**` | With Connector Key | Without it the task is written as a direct request and reported in `Data.Unresolved[]`. |

`isRequired`, `runOnlyOnce`, activation mode and entry rule come from the SDD task envelope, as for every task.

## Rules

1. **Never put a credential in `**Headers:**`.** An `Authorization`, API-key or cookie header in the SDD ships in `caseplan.case` and in every pull of it. Authenticate with `**Connector Key:**` + `**Connection ID:**` instead; if the SDD carries a credential, stop and ask the user to move it to a connection.
2. **No registry lookup.** An http-request task produces no `tasks/registry-resolved.json` entry. Connector mode's connection comes from the SDD's `**Connection ID:**`, the same id `uip is connections list` shows.
3. **Outputs are fixed.** The task's outputs are the response's `code`, `headers` and `body`, plus `Error`. An SDD Outputs row naming anything else is reported in `Data.Unresolved[]`. Downstream tasks read them per Rule 11, e.g. `"Stage"."Task".body`.

<!-- END: planning.md -->
