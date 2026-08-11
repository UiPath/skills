# Execute Non Query Failure — Driver / Client Library Not Loadable

This scenario reproduces a runtime `Execute Non Query` failure caused by
the **database client / driver native library being absent or the wrong
bitness** on the Robot host. The SQL, the connection string, and the
schema are all correct — the provider simply cannot load its native
client, so the native load fails with `Failed to load library
(ErrorCode: 126)` / `System.DllNotFoundException` before the statement
ever reaches the database.

## What this scenario uncovers

**Root Cause:** The `Execute Non Query` activity targets an Oracle
database with `ProviderName = "Oracle.DataAccess.Client"`, which depends
on the Oracle Client native libraries (`OraOps12.dll` and friends). The
Robot host either lacks those libraries or has them installed at a
bitness that does not match the **process**. The project's
`targetFramework` is `Windows` (a 64-bit process), so it needs the
**64-bit** Oracle Client; a 32-bit client does not satisfy it and
produces the same `ErrorCode: 126`.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-non-query-failures.md`
**Branch 4 (driver / client library not loadable)** — the same
driver/bitness family as `connect-to-database-failures.md` Branch 2.

> **Why "Branch 4":** the `Execute Non Query` playbook has four
> branches — output-parameter size (1), unsafe SQL / parameter mapping
> (2), empty `Sql` (3), and driver/client not loadable (4). The
> `ErrorCode: 126` + `DllNotFoundException` signature is unique to
> Branch 4. The fix lives on the host, not in the workflow.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Non Query with a well-formed parameterized `UPDATE` over the `Oracle.DataAccess.Client` provider |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The error log / job `Info`: `System.DllNotFoundException: Unable to load DLL 'OraOps12.dll' ... Failed to load library (ErrorCode: 126)` at the `Execute Non Query` step.
2. `Main.xaml` shows `ProviderName = "Oracle.DataAccess.Client"` (a native-client provider) with a well-formed parameterized `Sql` — proving the failure is the driver, not the statement.
3. `project.json` sets `targetFramework: Windows` (a 64-bit process), anchoring the bitness requirement (64-bit client).

## How this differs from sibling Execute Non Query branches

| Dimension | Branch 1 (output-param size) | Branch 2 (SQL construction) | Branch 3 (empty Sql) | Branch 4 (driver load — this) |
|---|---|---|---|---|
| Error anchor | `Size property has an invalid size of 0` | `A database error occurred` + inner syntax/type error | `CommandText property has not been initialized` | `Failed to load library (ErrorCode: 126)` / `DllNotFoundException` |
| `Sql` well-formed? | yes | no (concatenated / wrong type) | no (empty) | yes |
| Reaches the database? | yes | yes | no (ADO.NET refuses) | **no — provider never loads** |
| Where the fix lives | workflow (parameter `Size`) / package version | workflow (parameterize) | workflow (populate `Sql`) | **Robot host (install driver)** |

This scenario is one where the failing layer is **the host
environment** — the diagnosing user has Orchestrator access only and
cannot get on the Robot machine, so the agent must reach the root cause
from evidence and hand back a **host-side install instruction** (install
the matching-bitness driver, then verify with Configure Connection) —
not a workflow or SQL change.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook (Branch 4) AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) identify the missing / wrong-bitness DB driver / client library as the cause, (b) tie it to `ErrorCode 126` / `DllNotFoundException`, and (c) recommend installing the matching-bitness (64-bit) driver/client on the Robot host and verifying with Configure Connection — NOT a SQL, parameter, connection-string, or activity change

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-non-query-driver-load --apply
```
