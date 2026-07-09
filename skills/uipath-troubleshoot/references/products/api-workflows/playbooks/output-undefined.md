---
confidence: medium
---

# `$context.outputs.<Task>` Is Undefined Downstream

## Context

What this looks like:
- A downstream task reads `$context.outputs.<TaskName>` and gets `undefined`
- If-conditions that read a prior task's output always evaluate false; JS_Invoke scripts return empty; a Response field comes back empty
- No hard error — a silent wrong-result rather than a crash

What can cause it:
- **Prior task did not `export`.** Every non-Assign task must propagate state with `{ ...$context, outputs: { ...$context?.outputs, "<Key>": $output } }`. Without it, its output never lands in `$context.outputs`.
- **Connector (IntSvc-kind) output read at the root instead of `.content`.** A `UiPath.IntSvc` activity wraps the vendor payload under `.content` — the data is at `$context.outputs.<X>.content.<field>`, not `$context.outputs.<X>.<field>`. List-shaped ops put the array at `.content` (`.content[0].<field>`).
- **Slot key vs. export-bucket key mismatch (connector activities only).** For connector activities the `do`-array slot key and the `$context.outputs.<X>` bucket key can differ (e.g. slot `GetNewestEmail_1` / bucket `getNewestEmail_1`). Reading the wrong one returns `undefined`.
- **Wrong input accessor.** Reading a workflow input as `$input.<name>` instead of `$workflow.input.<name>` — `$input` is the *previous task's* output for any non-first task.

What to look for:
- Whether the referenced `<Task>` actually has an `export` block, and whether it's a connector activity (check `call: "UiPath.IntSvc"`/`"UiPath.Http"`)
- Whether the read goes through `.content` for connector outputs

## Investigation

1. Reproduce: `uip api-workflow run <Workflow.json> --no-auth --output json` and log the full output of the producing task once to inspect its real shape.
2. Confirm the producing task has an `export.as` that spreads `...$context?.outputs` and writes its own key.
3. For connector activities, compare the read path against the stub's `ExportBucketKey`, and check whether the value lives under `.content`.
4. For input reads, confirm the accessor is `$workflow.input.<name>`.

## Resolution

- **If missing export:** add the standard outputs export to the producing task; re-run.
- **If connector output:** read through `.content` — `$context.outputs.<bucket>.content.<field>` (or `.content[0].<field>` for arrays).
- **If key mismatch:** use the stub's `ExportBucketKey` verbatim in `export.as` and in every downstream reference.
- **If wrong accessor:** switch `$input.<name>` → `$workflow.input.<name>`, and confirm the input is declared in `input.schema` (or has a default) and was passed via `--input-arguments`.
