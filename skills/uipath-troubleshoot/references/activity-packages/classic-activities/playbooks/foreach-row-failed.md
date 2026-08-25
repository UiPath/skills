---
confidence: low
---

# For Each Row Failed

## Context

`For Each Row` (iterating a DataTable) faulted. The fault is usually not in the loop construct itself
but in the data it iterates or in an activity inside the loop body. `Log Message` rarely faults on
its own; when it appears in a stack it is normally relaying an error from elsewhere — investigate the
surrounding activity rather than the log call.

What this looks like:
- The loop throws at the start (before iterating) — typically a null/uninitialized DataTable
- A design-time validation error about the iterator (`CurrentRow`) variable name
- The loop runs and then throws on a particular row — the real error is an activity inside the body
  acting on that row's data

What can cause it:
- The DataTable is null/uninitialized because an upstream step (Read Range, Build Data Table, a query)
  did not produce it
- The iterator variable name is invalid (empty, starts with a digit, or contains characters other
  than letters/digits/underscore)
- An activity inside the loop body throws on a specific row — a missing/empty column value, a failed
  type conversion, an out-of-range access, or a downstream activity (UI, file, queue, etc.) failing

What to look for:
- Whether the DataTable passed to the loop was actually populated upstream
- Which iteration/row the failure occurred on (first row → setup/data problem; a later row →
  row-specific data)
- The innermost exception and which body activity raised it

## Investigation

1. Confirm the DataTable input is non-null and populated — trace the upstream step that builds/reads
   it.
2. If a validation error names the iterator variable, check the `CurrentRow` variable name against
   the naming rules.
3. Determine which row the failure happened on (fails immediately → setup/data; fails after some
   iterations → that row's data).
4. Read the innermost exception and identify which activity inside the body threw, then switch to
   that activity's signature/playbook.
5. Inspect the offending row's values (missing/empty columns, unexpected types) against what the body
   activities assume.

## Resolution

- **If the DataTable is null:** fix the upstream step so it produces a populated DataTable before the
  loop.
- **If the iterator name is invalid:** rename `CurrentRow` to a valid identifier (letters/digits/
  underscore, not starting with a digit).
- **If a body activity throws on a row:** diagnose that activity with its own playbook; handle the
  bad row's data (validate/convert columns, guard missing values).
- **If certain rows are expected to be incomplete:** validate/skip them explicitly inside the loop
  rather than letting the body throw.
