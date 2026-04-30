# Failure Modes — Pattern Catalog

Lookup table for known recurring failure modes in Maestro Flow projects. Each entry: what the failure looks like, why it happens, how to fix it, where to read more. Use this when you have an error symptom in hand and want to identify the pattern.

> **Hot-path triage:** if you have a failed run and need to investigate from scratch, start at [troubleshooting-guide.md](troubleshooting-guide.md) (the priority ladder: incidents → variables → flow correlation → traces). This document is the **lookup catalog** — read it after the ladder identifies a known pattern, or when the symptom matches an entry below.

## Index

| Pattern | Symptom | Cause |
|---|---|---|
| [MST-9107](#mst-9107--js-prefix-missing) | Activity input bound to literal string `"vars.X.output.Y"` | Missing `=js:` prefix on a `$vars` reference |
| [MST-9061](#mst-9061--misshapen-rectangle-nodes-in-studio-web) | Nodes render as oblong rectangles, not squares | `flow tidy` not run before publish |
| [HITL `completed` port unwired](#hitl-completed-port-unwired) | Flow hangs indefinitely after a HITL node | No outgoing edge from the node's `completed` source port |
| [Reused reference ID](#reused-reference-id--cross-connection-id-leakage) | Connector node faults silently at runtime | Reference ID copied from a prior flow's connection |
| [Single-nested layout](#single-nested-layout) | Studio Web upload fails; `uip solution project add` wiring breaks | `uip maestro flow init` was run outside a solution directory |
| [Missing `bindings[]` on resource node](#missing-bindings-on-resource-node) | `Folder does not exist or the user does not have access to the folder` | Top-level `bindings[]` entries not added for a `uipath.core.*` resource node |
| [`flow validate` passes, `flow debug` faults](#flow-validate-passes-flow-debug-faults) | Local validation green, cloud run red | Multiple causes — see entry for triage path |

---

## MST-9107 — `=js:` prefix missing

### Symptom

A connector, HTTP, or end node receives the literal string `"vars.X.output.Y"` as its input value at runtime instead of the resolved value. `flow validate` passes locally; the failure manifests only at `flow debug` or in deployed runs.

Example: input field set to literal `"vars.createEntityRecord1.output.Id"` instead of the entity's actual ID.

### Cause

The `=js:` prefix was omitted on a `$vars` / `$metadata` / `$self` reference inside a value field. The serializer rewrites `$vars` → `vars` whether or not the prefix is present, so a missing `=js:` yields a string that **looks like** an unevaluated expression but is actually a literal.

There is also no `nodes.X.output.Y` syntax — that is an invented form that silently ships as a literal string.

### Fix

Add `=js:` to every `$vars`/`$metadata`/`$self` reference in:

- Connector `inputs.detail.bodyParameters` / `queryParameters` / `pathParameters`
- HTTP `url` / `headers` / `body`
- End node output `source`
- Variable update `expression`
- Loop `collection`
- Subflow `inputs.<id>.source`

Do **not** add `=js:` to condition expressions (decision `expression`, switch case `expression`, HTTP branch `conditionExpression`) — those are evaluated as JavaScript automatically.

### Reference

[shared/node-output-wiring.md](../../shared/node-output-wiring.md) — canonical per-node-type field reference.

---

## MST-9061 — Misshapen rectangle nodes in Studio Web

### Symptom

After publish or debug upload, Studio Web renders nodes as oblong rectangles (e.g., 200×80) instead of square tiles. Layout looks visually broken even though the flow runs correctly.

### Cause

`uip maestro flow tidy` was not run before publishing or debugging. Hand-written or stale `layout` data with non-96 dimensions remains in the `.flow` file and Studio Web renders it as-is.

### Fix

Run tidy before any publish or debug operation:

```bash
uip maestro flow tidy <ProjectName>.flow --output json
```

Tidy:

- Sets every non-`stickyNote` node's `size` to `{ "width": 96, "height": 96 }`
- Arranges nodes horizontally with ELK at `nodeSpacing: 96`
- Recurses into subflows and rewrites `subflows[<id>].layout`
- Preserves sticky note custom sizes

### Reference

[author capability](../../author/CAPABILITY.md) — see "Always run `flow tidy` after edits" in critical rules; [shared/cli-commands.md — uip maestro flow tidy](../../shared/cli-commands.md#uip-maestro-flow-tidy).

---

## HITL `completed` port unwired

### Symptom

Flow execution reaches a HITL QuickForm node, the human task is created and completed, but the flow blocks indefinitely afterward. No further nodes execute.

### Cause

The HITL node's `completed` output handle has no outgoing edge — there is no consumer for the `completed` port event.

### Fix

Add an edge from the HITL node's `completed` port to the next node in the flow. After running `uip maestro flow hitl add`, always wire the `completed` port before validating.

### Reference

[author/plugins/hitl/impl.md](../../author/references/plugins/hitl/impl.md) — full HITL node reference including port wiring requirements.

---

## Reused reference ID — cross-connection ID leakage

### Symptom

A connector node passes `flow validate` and `node configure` cleanly. At runtime (`flow debug` or deployed run), the node faults silently with no resolvable error.

Common scenarios:

- A `parentFolderId` from one Outlook mailbox used in a flow connected to a different Outlook mailbox
- A Slack channel ID from one workspace used in a flow connected to a different Slack workspace
- A Jira project key copied from a prior session

### Cause

Reference IDs (mailbox folders, Slack channels, Jira projects, Google Sheets, etc.) are **scoped to the specific authenticated account behind the connection**. They are not portable across connections, even when the connection points to the same connector type.

### Fix

Always re-resolve reference IDs against the connection bound to the current flow. Never paste a value you saw in another flow or session:

```bash
uip is resources execute list <connector-key> <objectName> --connection-id <CURRENT_CONNECTION_ID> --output json
```

### Reference

- [author/plugins/connector/impl.md — Step 4](../../author/references/plugins/connector/impl.md)
- [author/plugins/connector-trigger/impl.md — Step 3](../../author/references/plugins/connector-trigger/impl.md)

---

## Single-nested layout

### Symptom

`uip solution upload` rejects the project. `uip solution project add` cannot wire the project to the solution. Studio Web upload fails with structural errors. Packaging fails.

The `.flow` file lives at `<Project>/<Project>.flow` (single-nested) instead of the required `<Solution>/<Project>/<Project>.flow` (double-nested).

### Cause

`uip maestro flow init` was run from outside a solution directory — from a bare cwd, from the user's home directory, or from the parent of the solution.

### Fix

Delete the partial scaffold. Restart in the correct order:

```bash
uip solution new "<SolutionName>" --output json
cd <SolutionName>
uip maestro flow init <ProjectName>
uip solution project add <SolutionName>/<ProjectName> <SolutionName>/<SolutionName>.uipx
```

After running, verify the file exists at the double-nested path:

```bash
ls "<SolutionName>/<ProjectName>/<ProjectName>.flow"
```

If not, the `init` step was wrong — do not try to patch the layout by hand.

### Reference

[author/greenfield.md — Step 2](../../author/references/greenfield.md) — the canonical scaffold sequence.

---

## Missing `bindings[]` on resource node

### Symptom

`uip maestro flow validate` passes locally. At `uip maestro flow debug` (or in deployed runs), the resource node faults with:

```text
Folder does not exist or the user does not have access to the folder.
```

The error mentions a folder, but the actual cause is a missing binding entry.

### Cause

For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the registry definition carries `model.context[]` with `<bindings.{name}>` placeholders. The runtime rewrites these to `=bindings.{id}` at BPMN emit by matching `(resourceKey, name)` against the **top-level `bindings[]` array** in the `.flow` file. Without those entries, the placeholder never resolves and the runtime treats the binding as missing — surfacing as the folder-not-found error.

`flow validate` checks JSON schema and cross-references; it does not validate that resource-node `model.context[]` entries are matched by top-level `bindings[]` entries.

### Fix

Add two entries to the top-level `bindings[]` array per resource node — `name` and `folderPath` — with `resourceKey` matching the definition's `model.bindings.resourceKey`. See the relevant resource plugin's `impl.md` for the exact shape ([rpa](../../author/references/plugins/rpa/impl.md), [agent](../../author/references/plugins/agent/impl.md), [flow](../../author/references/plugins/flow/impl.md), [agentic-process](../../author/references/plugins/agentic-process/impl.md), [api-workflow](../../author/references/plugins/api-workflow/impl.md), [hitl](../../author/references/plugins/hitl/impl.md)).

### Reference

[shared/file-format.md — Bindings](../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings)

---

## `flow validate` passes, `flow debug` faults

### Symptom

Local `uip maestro flow validate` returns `Result: Success`. The same flow fails at `uip maestro flow debug` with a runtime error.

### Cause

Multiple. `flow validate` is a JSON schema + cross-reference check; it does not catch:

- Missing `=js:` prefix → see [MST-9107](#mst-9107--js-prefix-missing)
- Reused reference IDs → see [Reused reference ID](#reused-reference-id--cross-connection-id-leakage)
- Missing top-level `bindings[]` entries on resource nodes → see [Missing `bindings[]` on resource node](#missing-bindings-on-resource-node)
- Connector input fields with hand-written `inputs.detail` (missing `essentialConfiguration` block) — re-run `uip maestro flow node configure` to populate properly
- HITL `completed` port unwired → see [HITL `completed` port unwired](#hitl-completed-port-unwired)
- Stale `layout` data → see [MST-9061](#mst-9061--misshapen-rectangle-nodes-in-studio-web) (cosmetic, not faulting)

### Fix

Triage via the diagnostic priority ladder in [troubleshooting-guide.md](troubleshooting-guide.md). Match the incident message and faulting element to the patterns above.

### Reference

[troubleshooting-guide.md](troubleshooting-guide.md) — start there for any "passes locally, fails in cloud" scenario.
