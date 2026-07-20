---
confidence: medium
---

# `$context.outputs.<Activity>` Is Undefined Downstream

## Context

Each activity's output is read downstream as `$context.outputs.<Activity>`, where `<Activity>` is the activity's output name (defaults to its id, e.g. `HTTP_1`, `For_Each_1`).

What this looks like — two symptom shapes, same fault family:
- **Hard crash** — `Cannot read properties of undefined (reading '<Activity>')`: `$context.outputs` itself doesn't exist because no upstream activity has exported yet. The `(reading '<Activity>')` fragment names the key the reader expected.
- **Silent `undefined`** — `$context.outputs` exists (some activity has exported) but the key doesn't match: If-conditions that read a prior activity's output always evaluate false, JS_Invoke scripts return empty, a Response field comes back empty — no hard error.

What can cause it:
- **Producing activity did not `export`.** Every non-Assign activity must propagate state with `{ ...$context, outputs: { ...$context?.outputs, "<Activity>": $output } }`. Without it, its output never lands in `$context.outputs` — and if no other activity has exported either, `$context.outputs` never comes into existence and the downstream read crashes instead of returning `undefined`.
- **Connector (IntSvc-kind) output read at the root instead of `.content`.** A `UiPath.IntSvc` activity wraps the vendor payload under `.content` — the data is at `$context.outputs.<Activity>.content.<field>`, not `$context.outputs.<Activity>.<field>`. List-shaped ops put the array at `.content` (`.content[0].<field>`).
- **Slot key vs. export-bucket key mismatch (connector activities only).** For connector activities the `do`-array slot key and the `$context.outputs.<Activity>` export-bucket key can differ (e.g. slot `GetNewestEmail_1` / bucket `getNewestEmail_1`). Reading the wrong one returns `undefined`.
- **Wrong input accessor.** Reading a workflow input as `$input.<name>` instead of `$workflow.input.<name>` — `$input` is the *previous activity's* output for any non-first activity.

What to look for:
- Whether the referenced `<Activity>` actually has an `export` block, and whether it's a connector activity (check `call: "UiPath.IntSvc"`/`"UiPath.Http"`)
- Whether the read goes through `.content` for connector outputs

## Investigation

1. Reproduce: `uip api-workflow run <Workflow.json> --no-auth --output json` and log the full output of the producing activity once to inspect its real shape.
2. Confirm the producing activity has an `export.as` that spreads `...$context?.outputs` and writes its own key.
3. For connector activities, two checks:
   - **Read key:** the key in the downstream `$context.outputs.<Activity>` read must equal the key string written inside the producing activity's `export.as` (`outputs: { ..., "<Activity>": $output }`) — not the activity's `do`-array slot key, which can differ from it for connector activities.
   - **Read path:** connector output is a wrapper — the read must go through `.content`: `$context.outputs.<Activity>.content.<field>`.
4. For input reads, confirm the accessor is `$workflow.input.<name>`.

## Resolution

- **If missing export:** add the standard outputs export to the producing activity; re-run.
- **If connector output:** read through `.content` — `$context.outputs.<Activity>.content.<field>` (or `.content[0].<field>` for arrays).
- **If key mismatch:** regenerate the activity stub (`uip api-workflow registry stub --output json`) and use its `Data.ExportBucketKey` verbatim in `export.as` and in every downstream reference.
- **If wrong accessor:** switch `$input.<name>` → `$workflow.input.<name>`, and confirm the input is declared in `input.schema` (or has a default) and was passed via `--input-arguments`.
