# Execute Query Failure — Null / Out-of-Scope Connection

This scenario reproduces a runtime `Execute Query` failure caused by a
`DatabaseConnection` variable that is **out of scope** where the query
runs. `Connect to Database` opens the connection inside a nested
`Sequence`, but `Execute Query` sits outside that sequence — so by the
time it executes, the connection variable is `Nothing`. The activity
throws `System.NullReferenceException` ("Object reference not set to an
instance of an object").

## What this scenario uncovers

**Root Cause:** The `Execute Query` activity reads `ExistingDbConnection`
from `dbConnection`, a variable declared on a nested `Sequence`
("Open Connection") that also hosts the `Connect to Database` activity.
Once execution leaves that inner sequence the variable is disposed and
out of scope; `Execute Query`, in the parent sequence, receives a null
connection and faults.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
— **Branch 1 — null / out-of-scope connection** (medium-confidence
playbook).

> **Why "medium-confidence":** `NullReferenceException` at the activity
> is the verbatim Branch 1 signature, but Branch 1 has several
> sub-causes (connect never ran, wrong/unwired variable, out-of-scope
> variable, disposed handle). The agent must trace the connection
> variable in the workflow source to land on the scope sub-cause.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — `Connect to Database` inside a nested `Sequence`, `Execute Query` outside it referencing the out-of-scope variable |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The job exception: `System.NullReferenceException: Object reference not set to an instance of an object.` thrown `at ExecuteQuery "Execute Query"`.
2. The job-log Trace ordering: `Connect to Database` ran and opened the connection, the inner `Sequence "Open Connection"` then closed (disposing `dbConnection`), and only afterward did `Execute Query` start and fault.
3. The workflow source (`Main.xaml`): `dbConnection` is declared on the nested `Sequence`, while `Execute Query` lives in the parent `Sequence` — the scope mismatch.

## How this differs from sibling Execute Query branches

| Dimension | Branch 1 (this) | Branch 2 | Branch 3 | Branch 5 | Branch 7 |
|---|---|---|---|---|---|
| Failure | null/out-of-scope connection | provider mismatch (post-migration) | SQL syntax / concatenation | command timeout | wrong activity for statement |
| Signature | `NullReferenceException` | `Keyword not supported` | `A database error occurred` (inner syntax) | `Timeout expired` | empty/cast error |
| Fix layer | workflow (variable scope) | provider config | parameterize SQL | `TimeoutMS` / index | swap activity |

The agent must recommend fixing the **connection variable's scope** in
the workflow — not the SQL, the provider, the timeout, or the activity
type.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the Execute Query failures playbook (Branch 1) AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) identify the `DatabaseConnection` as null / out of scope, (b) attribute it to the connection variable being declared inside the nested `Sequence`, and (c) recommend declaring the variable at the enclosing scope (or moving `Execute Query` into the connect scope) and confirming the `ExistingDbConnection` wiring

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-query-null-connection --apply
```
