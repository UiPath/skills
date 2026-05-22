# Failure Modes — Pattern Catalog

Lookup table for known recurring failure modes in Maestro Flow projects. Each entry: what the failure looks like, why it happens, how to fix it, where to read more. Use this when you have an error symptom in hand and want to identify the pattern.

> **Hot-path triage:** if you have a failed run and need to investigate from scratch, start at [troubleshooting-guide.md](troubleshooting-guide.md) (the priority ladder: incidents → variables → flow correlation → traces). This document is the **lookup catalog** — read it after the ladder identifies a known pattern, or when the symptom matches an entry below.

## Index

| Pattern | Symptom | Cause |
|---|---|---|
| [MST-9107](#mst-9107--js-prefix-missing) | Activity input bound to literal string `"vars.X.output.Y"` | Missing `=js:` prefix on a `$vars` reference. `flow validate` catches this — pre-`expression-prefix-validator` cli still ships the literal at runtime. |
| [MST-9972](#mst-9972--variablesnodes-missing-vars-resolves-to-undefined) | `Cannot read property 'output' of undefined` on a downstream node | Direct-authored `.flow` skipped `variables.nodes[]`; `flow validate` accepts it but the BPMN has no process-level variable declaration for the upstream node. |
| [MST-9061](#mst-9061--misshapen-rectangle-nodes-in-studio-web) | Nodes render as oblong rectangles, not squares | `flow format` not run before publish |
| [HITL `completed` port unwired](#hitl-completed-port-unwired) | Flow hangs indefinitely after a HITL node | No outgoing edge from the node's `completed` source port |
| [Reused reference ID](#reused-reference-id--cross-connection-id-leakage) | Connector node faults silently at runtime | Reference ID copied from a prior flow's connection |
| [Single-nested layout](#single-nested-layout) | Studio Web upload fails; `flow init` auto-registration is skipped | `uip maestro flow init` was run outside a solution directory |
| [Missing `bindings[]` on resource node](#missing-bindings-on-resource-node) | `Folder does not exist or the user does not have access to the folder` | Top-level `bindings[]` entries not added for a `uipath.core.*` resource node |
| [`flow validate` passes, `flow debug` faults](#flow-validate-passes-flow-debug-faults) | Local validation green, cloud run red | Multiple causes — narrower than before (MST-9107 + expression-ref linting now catch a large slice statically). See entry for the residual triage path. |

---

## MST-9107 — `=js:` prefix missing

### Symptom

A connector, HTTP, or end node receives the literal string `"vars.X.output.Y"` as its input value at runtime instead of the resolved value.

`flow validate` flags this as an error today (cli-side `expression-prefix-validator`, emitted with a remediation hint pointing at the `=js:`-prefixed form). Pre-validator cli versions miss it and the failure surfaces only at `flow debug` or in deployed runs — if you see the symptom without a corresponding validate error, your cli is older than the fix.

Example: input field set to literal `"vars.createEntityRecord1.output.Id"` instead of the entity's actual ID.

### Cause

The `=js:` prefix was omitted on a `$vars` / `$metadata` / `$self` reference inside a value field. The serializer rewrites `$vars` → `vars` whether or not the prefix is present, so a missing `=js:` yields a string that **looks like** an unevaluated expression but is actually a literal.

There is also no `nodes.X.output.Y` syntax — that is an invented form that silently ships as a literal string. `flow validate` flags this same way (rewriting the suggested fix to the `=js:$vars.X.output.Y` form).

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

## MST-9972 — `variables.nodes[]` missing → `$vars.X.output` resolves to undefined

### Symptom

A downstream script or expression reads `$vars.<sourceNodeId>.output` and gets `undefined` at runtime. Common shapes: `Cannot read property 'output' of undefined`, `Cannot read properties of undefined (reading '<field>')`, or a connector activity receiving an empty / undefined input that an upstream node should have populated. `uip maestro flow validate` accepts the file without complaint. The upstream node's own incident shows it ran successfully.

### Cause

The `.flow` file is missing `variables.nodes[]` entries for the upstream node. The BPMN emitter walks `variables.nodes[]` to write the process-level `<uipath:inputOutput id="<nodeId>.<outputId>">` declarations the runtime needs — without them, the activity's local `output` value has no process variable to flow into, and downstream `$vars` reads fail.

This happens almost exclusively on **direct-authored** `.flow` files: `uip maestro flow node add` and the canvas / Studio Web save path both auto-populate `variables.nodes[]`. `Edit` / `Write` authoring does not, and pre-fix `uip maestro flow format` did not regenerate it either. Adding an `outputs` block on the action-node instance does **not** fix this — for action nodes the BPMN emitter reads the manifest's `outputDefinition`, not the instance block, so authoring the instance block has no runtime effect.

### Fix

Run `uip maestro flow format <ProjectName>.flow --output json`. Post-MST-9972 the format command regenerates `variables.nodes[]` from `nodes[]` + `definitions[]` (matching `node add` and canvas behavior). On older CLI versions, add the entries manually:

```json
"variables": {
  "nodes": [
    {
      "id": "<nodeId>.output",
      "type": "object",
      "binding": { "nodeId": "<nodeId>", "outputId": "output" }
    },
    {
      "id": "<nodeId>.error",
      "type": "object",
      "binding": { "nodeId": "<nodeId>", "outputId": "error" }
    }
  ]
}
```

One entry per declared output (trigger nodes: `output` only; action nodes: `output` + `error`; end / terminate: none).

### Reference

[shared/file-format.md — Node outputs](../../shared/file-format.md#node-outputs), [author/CAPABILITY.md rule #14](../../author/CAPABILITY.md), [editing-operations-json.md — Pre-flight Checklist step 5–6](../../author/references/editing-operations-json.md#pre-flight-checklist).

---

## MST-9061 — Misshapen rectangle nodes in Studio Web

### Symptom

After publish or debug upload, Studio Web renders nodes as oblong rectangles (e.g., 200×80) instead of square tiles. Layout looks visually broken even though the flow runs correctly.

### Cause

`uip maestro flow format` was not run before publishing or debugging. Hand-written or stale `layout` data with non-96 dimensions remains in the `.flow` file and Studio Web renders it as-is.

### Fix

Run format before any publish or debug operation:

```bash
uip maestro flow format <ProjectName>.flow --output json
```

Format:

- Sets every non-`stickyNote` node's `size` to `{ "width": 96, "height": 96 }`
- Arranges nodes horizontally with ELK at `nodeSpacing: 96`
- Recurses into subflows and rewrites `subflows[<id>].layout`
- Preserves sticky note custom sizes

### Reference

[author capability](../../author/CAPABILITY.md) — see "Always run `flow format` after edits" in critical rules; [shared/cli-commands.md — uip maestro flow format](../../shared/cli-commands.md#uip-maestro-flow-format).

---

## HITL `completed` port unwired

### Symptom

Flow execution reaches a HITL QuickForm node, the human task is created and completed, but the flow blocks indefinitely afterward. No further nodes execute.

### Cause

The HITL node's `completed` output handle has no outgoing edge — there is no consumer for the `completed` port event.

### Fix

Add an edge from the HITL node's `completed` port to the next node in the flow. After running `uip maestro flow hitl add`, always wire the `completed` port before validating.

### Reference

[Author HITL plugin reference](../../author/references/plugins/hitl/impl.md) — full HITL node reference including port wiring requirements.

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
uip is resources run list <connector-key> <objectName> --connection-id <CURRENT_CONNECTION_ID> --output json
```

### Reference

- [Author connector plugin — Step 4](../../author/references/plugins/connector/impl.md)
- [Author connector-trigger plugin — Step 3](../../author/references/plugins/connector-trigger/impl.md)

---

## Single-nested layout

### Symptom

`uip solution upload` rejects the project. `flow init` returned without a `Data.SolutionRegistration` block (auto-registration walks up looking for the nearest `.uipx`; when the project is created outside the solution, it finds none and skips silently). Studio Web upload fails with structural errors. Packaging fails.

The `.flow` file lives at `<Project>/<Project>.flow` (single-nested) instead of the required `<Solution>/<Project>/<Project>.flow` (double-nested).

### Cause

`uip maestro flow init` was run from outside a solution directory — from a bare cwd, from the user's home directory, or from the parent of the solution.

### Fix

Delete the partial scaffold. Restart in the correct order — `flow init` from inside the solution directory will auto-register the project with the `.uipx`, so the explicit `uip solution project add` step is no longer needed.

```bash
uip solution init "<SolutionName>" --output json
cd <SolutionName>
uip maestro flow init <ProjectName> --output json
# Confirm Data.SolutionRegistration.Status is "Registered" in the JSON response.
# Only if Status is "Skipped" / "Failed" do you need:
#   uip solution project add <SolutionName>/<ProjectName> <SolutionName>/<SolutionName>.uipx
```

After running, verify the file exists at the double-nested path. The `cd <SolutionName>` above persists across Bash calls, so anchor the check with `$(pwd)` instead of repeating `<SolutionName>/`:

```bash
ls "$(pwd)/<ProjectName>/<ProjectName>.flow"
```

A relative `ls "<SolutionName>/<ProjectName>/<ProjectName>.flow"` here resolves to `<SolutionName>/<SolutionName>/<ProjectName>/<ProjectName>.flow` (triple-nested) and reports "no such file" even on a correctly-scaffolded solution — a false negative that turns a healthy layout into a fake bug.

If the absolute path doesn't exist, the `init` step was wrong — do not try to patch the layout by hand.

### Reference

[Author greenfield journey — Step 2](../../author/references/greenfield.md) — the canonical scaffold sequence.

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

Multiple. `flow validate` runs a JSON schema check, cross-reference checks, expression-reference linting, and a small set of structural rules.

**Caught** (validate exits non-zero, with a precise field path and remediation hint):

- Missing `=js:` prefix on `$vars`/`$metadata`/`$self` (MST-9107) — emitted by cli-side `expression-prefix-validator`
- Invented `nodes.<id>.output.<...>` syntax (MST-9107 variant) — same validator, suggests `=js:$vars.<id>.output.<...>` as the fix
- References to unknown variable IDs or node IDs in `=js:` expressions (`EXPR_UNRESOLVED_REF`) — flow-schema `expression-ref` rule
- Output-path walks that descend into a declared primitive (`type: "string"` etc.) or a schema closed with `additionalProperties: false` (`EXPR_INVALID_OUTPUT_PATH`) — flow-schema `expression-ref` rule
- Missing End-node output mappings for declared `out` variables (`MISSING_OUTPUT_MAPPING`, **warning** severity) — flow-schema `output-mapping` rule
- Connector `inputs.detail.configuration` missing, empty, missing the `essentialConfiguration` envelope, or containing invalid JSON inside the `=jsonString:` prefix — emitted with a shape hint pointing at `uip maestro flow node configure`. Re-run that command rather than hand-editing.

**Not caught** — these still surface only at `flow debug` or in deployed runs:

- Reused reference IDs → see [Reused reference ID](#reused-reference-id--cross-connection-id-leakage)
- Missing top-level `bindings[]` entries on resource nodes → see [Missing `bindings[]` on resource node](#missing-bindings-on-resource-node)
- HITL `completed` port unwired → see [HITL `completed` port unwired](#hitl-completed-port-unwired)
- Stale `layout` data → see [MST-9061](#mst-9061--misshapen-rectangle-nodes-in-studio-web) (cosmetic, not faulting)
- Output-path walks against **open** output schemas — HTTP response bodies, script returns, free-text agent output. The deep-path walker is permissive by design: it skips when the producer's schema doesn't authoritatively declare the field's structure, so e.g. `=js:$vars.fetchWeather.output.body.current_weather` against an HTTP node that declares only `output: { type: "object" }` passes validate and faults only when the runtime response doesn't have that path.
- Wrong-direction reads (reading an `out`-only variable) — currently a runtime concern; the direction discriminator isn't yet threaded into the validator context.

### Fix

Triage via the diagnostic priority ladder in [troubleshooting-guide.md](troubleshooting-guide.md). Match the incident message and faulting element to the patterns above.

### Reference

[troubleshooting-guide.md](troubleshooting-guide.md) — start there for any "passes locally, fails in cloud" scenario.
