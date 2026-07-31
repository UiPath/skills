# Execute Non Query Failure — Empty Sql (CommandText not initialized)

This scenario reproduces a runtime `Execute Non Query` failure caused by
an **empty `Sql`**. The activity's `Sql` property is bound to an
expression that resolves to `""` at runtime, so ADO.NET rejects the
command with `CommandText property has not been initialized`. The
database, connection, driver, and SQL syntax are all fine — the command
simply has no text.

## What this scenario uncovers

**Root Cause:** The `Execute Non Query` activity in `Main.xaml` has
`Sql="[sqlText]"`. The upstream Assign sets `sqlText` from
`dt_Config.Rows[0]["UpdateStatement"]` only when the table has rows,
falling back to `""`. At runtime `dt_Config` is empty, so `sqlText`
stays blank and the activity faults with `CommandText property has not
been initialized`.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-non-query-failures.md`
(**Branch 3 — Empty `Sql`**).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — `Execute Non Query` with `Sql` bound to a variable that resolves empty |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The `or jobs get` Info / `or jobs logs` error: `Execute Non Query: A database error occurred. CommandText property has not been initialized.`
2. The job-log trace `About to run Execute Non Query. SQL: ''` (preceded by `dt_Config row count: 0`) — proof the resolved `Sql` is empty.
3. `Main.xaml` shows `Sql="[sqlText]"` (an expression, not a literal) and the upstream Assign that leaves `sqlText` blank when the DataTable is empty.

## How this differs from sibling Execute Non Query branches

| Dimension | Branch 1 (output-param size) | Branch 2 (SQL syntax / params) | Branch 3 — empty Sql (this) | Branch 4 (driver load) |
|---|---|---|---|---|
| Error signature | `Size property has an invalid size of 0` | `A database error occurred` wrapping syntax/type error | `CommandText property has not been initialized` | `Failed to load library (ErrorCode: 126)` |
| `Sql` present? | yes (proc name) | yes (malformed) | **no — resolves to ''** | yes |
| Connection opened? | yes | yes | yes | no (load fails) |
| `CommandType` | StoredProcedure | Text | **Text** | any |
| Fix layer | Parameter `Size` | Parameterize statement | **Sql expression + upstream source/scope** | Host driver/bitness |

The agent must reject SQL-syntax error, output-parameter sizing,
driver-not-loaded, null connection, wrong activity, and database outage,
and land specifically on the empty/unset `Sql` (Branch 3).

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (Branch 3) AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) identify the `Sql` as empty/unset (`CommandText property has not been initialized`), (b) cite the empty resolved SQL in the logs and the expression-bound `Sql` in source, and (c) recommend ensuring `Sql` resolves non-empty (log + fix the upstream assignment / variable scope)

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-non-query-empty-sql --apply
```
