# Execute Query Failure — Command Timeout Exceeded (Runaway Un-indexed Query)

This scenario reproduces a runtime `Execute Query` failure caused by a
**query that exceeds the activity's `TimeoutMS`**. The activity runs an
expensive, un-indexed statement; the provider performs a full-table scan,
runs past the timeout, and aborts. Orchestrator surfaces
`Execute Query: Timeout expired. The timeout period elapsed prior to
completion of the operation or the server is not responding.`

## What this scenario uncovers

**Root Cause:** The `Execute Query` activity's `Sql` is
`SELECT * FROM Orders WHERE UPPER(Notes) LIKE '%...%'`. `UPPER(Notes)`
under a leading-wildcard `LIKE` is not sargable and `Orders` has no index
on `Notes`, so the provider does a full-table scan. `TimeoutMS` is left at
the default `30000` (30 s, **milliseconds**); the scan runs past 30 s and
the provider aborts with `Timeout expired`. The fix has two tiers: the
**real fix** is fixing the query/index (sargable predicate + supporting
index, narrower result set); raising `TimeoutMS` (in milliseconds) is only
a **stopgap** because it just delays the same failure on a runaway query.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 5 — command timeout exceeded).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Query with default `TimeoutMS` running an un-indexed full-scan query behind a valid Connect/Execute structure |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-5 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Sales Automation` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `OrderNotesSearch` job (ran ~30 s ≈ `TimeoutMS`).
3. `uip or jobs get <job-key> --output json` → `Info` carries `Execute Query: Timeout expired. The timeout period elapsed prior to completion of the operation or the server is not responding.`
4. `uip or jobs logs <job-key> --output json` → Trace lines showing the connection opened, the query started with `TimeoutMS=30000`, then `command aborted after 30000 ms ... full-table scan` — the smoking gun proving the query duration exceeded the timeout.
5. `process/Main.xaml` → the `Execute Query` `Sql` is the un-indexed `UPPER(Notes) LIKE '%...%'` scan with `TimeoutMS="30000"` (default).

## How this differs from sibling branches

| Dimension | branch 1 (null connection) | branch 3 (concatenation) | branch 5 (timeout) (this) |
|---|---|---|---|
| Connection opens? | no | yes | **yes** |
| SQL valid? | n/a | no (malformed) | **yes (just slow)** |
| Error signature | `NullReferenceException` | `A database error occurred` + `Incorrect syntax near ...` | **`Timeout expired ...`** |
| Where the fault is | wiring/scope | the SQL text | **query DURATION vs `TimeoutMS`** |
| Fix | wire/scope the connection | parameterize the query | **fix the index/query (real); raise `TimeoutMS` (stopgap)** |

The failing layer here is the **query duration exceeding `TimeoutMS`**,
not the connection, the driver, the statement text, or a DB outage. The
agent must recognize this is a runaway un-indexed query — so the real fix
is the index/query, and raising `TimeoutMS` (in milliseconds) is only a
temporary stopgap. It must not blame a null connection, SQL syntax, a
provider mismatch, a CLR crash, the wrong activity, or "the database is
down".

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (Branch 5) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) name the `Timeout expired` failure at Execute Query, (b) attribute it to the query running longer than `TimeoutMS` because it is a runaway un-indexed full-table scan, and (c) recommend the real fix = add an index / narrow the query, noting raising `TimeoutMS` (milliseconds) is only a stopgap.
- Partial credit (0.8) if the agent matches the timeout branch but treats it as a legitimately long query and recommends only raising `TimeoutMS`.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-query-timeout-expired --apply
```
