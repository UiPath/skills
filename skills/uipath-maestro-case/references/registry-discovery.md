# Registry Discovery Reference

Read this file only when the Planner-authored SDD names tenant resources that
must be resolved before JSON lowering. The SDD is authoritative. Registry data
adds runtime identity and schema; it never redesigns the case.

## Contract

Resolve every external resource in one pass and write the evidence to
`case-build/registry-resolved.json`. Do not create an intermediate plan.

For every resource, retain:

```json
{
  "stage": "<SDD stage>",
  "task": "<SDD task or trigger>",
  "taskType": "<closed case type>",
  "requested": {
    "name": "<SDD resource name>",
    "folder": "<SDD folder or null>",
    "identity": "<SDD identity or <UNRESOLVED>>"
  },
  "cacheFile": "<cache path or null>",
  "searchQuery": "<exact normalized query>",
  "matches": [],
  "selected": null,
  "ioContract": null,
  "status": "resolved|unresolved|placeholder|created",
  "rationale": "<deterministic selection reason>",
  "review_items": []
}
```

The evidence file is a disposable cache. On SDD identity/name/folder/type
mismatch, discard that entry and resolve it again.

## Prerequisites

1. Complete `uip auth` if needed.
2. Run `uip registry pull --output json` once per build session.
3. Use the cache files under `.uipath/registry/`. Do not query the tenant once
   per task.
4. When creation is selected, ensure the solution exists and probe local
   registration once:

   ```bash
   uip registry list --local --output json
   ```

## Cache File Index

| Case dependency | Cache file |
|---|---|
| `action` | `action-apps-index.json` |
| `agent` | `agents-index.json` |
| `api-workflow` | `api-workflows-index.json` |
| `process` / `rpa` | `processes-index.json` |
| `case-management` | `cases-index.json` |
| Connector activity / trigger / connector condition | TypeCache plus Integration Service discovery |

If an expected index is absent after a successful pull, record `matches: []`
with an absent-cache rationale. Do not fabricate an empty file or scan unrelated
indexes.

## Procedure

### 1. Build the lookup batch

Read the normalized SDD contract emitted by `inspect-sdd`. Deduplicate lookups
by `(taskType, resource name, folder)`. Preserve every referring stage/task in
the evidence entry so one resolution can serve identical consumers.

### 2. Search by exact identity, name, and folder

Use this precedence:

1. exact SDD identity when concrete;
2. exact normalized name plus exact folder;
3. exact normalized name when the SDD omitted folder.

Never select a fuzzy first match. One match resolves. Multiple matches remain
unresolved until a concrete identity/folder disambiguates them.

### 3. Fetch the runtime contract

For the selected resource, use the owning CLI's read-only describe/spec command
and retain required inputs, outputs, type identity, version, and connector
metadata in `ioContract`. Every command whose output is parsed must use
`--output json`.

For connectors, also retain connector key, connection ID, activity/trigger type
ID, object name when applicable, event operation/mode, and the resolved input
contract. Then follow [connector-trigger-guide.md](connector-trigger-guide.md)
or [connector-integration.md](connector-integration.md).

### 4. Gate all missing resources once

After the entire lookup batch finishes, present one grouped decision instead of
interrupting once per task.

## MUST Confirm Before Placeholder Fallback

Classify misses into:

- **Creatable here:** only `agent` and `api-workflow`.
- **Not creatable here:** action apps, processes/RPA, case plans, connectors,
  connections, and every other dependency.

Ask one batched question:

1. Create the selected missing agents/API workflows, and use placeholders for
   the rest.
2. Use placeholders for all unresolved resources.
3. Stop and let the user register resources externally.

Never initialize a solution, create a resource, or fall back to placeholders
before this gate.

## Create-on-Missing build and rediscovery

### 0 — Prerequisite and capability probe

Only after the user chooses Create, initialize the solution if it is absent and
confirm local registry support with `uip registry list --local --output json`.

### 1 — Select

Create only the explicitly selected missing `agent` and `api-workflow`
resources. All other misses follow the placeholder/stop choice.

### 1b — Choose build kind

Use the resource owner's native kind. Do not silently replace an agent with a
process, or an API workflow with a connector activity.

### 1c — Dedup the selected builds (one resource per name and type)

Merge only when type, normalized name, and declared I/O are identical. If two
SDD tasks reuse the same name with incompatible I/O, stop with a deterministic
conflict instead of creating two ambiguous resources.

### 2 — Build

Delegate each selected resource to its owning sibling skill with a compact
brief containing the SDD description, declared I/O, name, and all referring
case tasks. Build in parallel when safe, but skip registration inside the
delegated build.

If the sibling skill is unavailable, return an actionable unresolved entry and
continue according to the user's fallback choice. The Case skill must remain
self-contained.

### 3 — Register

Register successful builds sequentially. Never register two resources
concurrently into the same solution.

### 3b — "Already exists" means adopt and verify

An interrupted prior run may have built the sibling already. Discover it by
exact name and type, verify its I/O contract, and adopt it. An incompatible
existing resource is a conflict, not success.

### 4 — Rediscover, verify, and bind

Run `uip registry list --local --output json`, rediscover each created/adopted
resource, verify its declared I/O, update the evidence entry to `created`, and
bind the concrete identity into the lowering model. A created resource that
cannot be rediscovered or whose I/O differs is rejected and must not be
referenced by `caseplan.json`.

## Placeholder boundary

A placeholder preserves the SDD's intended task name/type and unresolved
resource metadata; it does not invent an identity. Follow
[placeholder-tasks.md](placeholder-tasks.md) for the JSON shape and later
upgrade procedure.

## Output Contract

Write one deterministic JSON document:

```json
{
  "sdd": "<path>",
  "sddSha256": "<content digest>",
  "generatedAt": "<ISO-8601 timestamp>",
  "resources": [],
  "summary": {
    "resolved": 0,
    "created": 0,
    "placeholder": 0,
    "unresolved": 0
  }
}
```

Sort `resources` by SDD order. The timestamp is evidence only; comparison and
resume logic use `sddSha256` and the normalized resource key. Never put secrets,
tokens, connection credentials, or full tenant dumps in the file.

<!-- END: registry-discovery.md -->
