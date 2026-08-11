# If — Wrong Branch Taken at Runtime (Case-Sensitive Comparison)

Runtime troubleshooting scenario for `System.Activities.Statements.If` — a silent logic fault.

## What this scenario exercises

An unattended job completes **Successful** but produces the wrong outcome: every approved order is
routed to the manual review queue. The agent must trace it to the `If` "Check approval decision", whose
Condition `decision = "Approved"` is a case-sensitive VB string comparison — the source system sent
`APPROVED`, so `"APPROVED" = "Approved"` is `False` and the Else (manual review) branch runs. The fix is
a case-insensitive, trimmed comparison. There is no exception — the agent must reason from the branch
that ran vs the branch expected, not from an error string.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted VB project source: `Main.xaml` with an `If` "Check approval decision" whose Condition is `decision = "Approved"` (exact-case, no `.Trim()`), Else branch logs "Routing to manual review queue" |
| `data/m/r/*.json` | **Successful**-job fixtures — `job-get` state `Successful` (no error code); `job-logs` show `Decision from source system: APPROVED` immediately followed by `Routing to manual review queue` (approved value → wrong branch); `job-traces` empty |
| `data/m/r/manifest.json` | `docsai ask` passthrough + `or jobs/folders` fixtures + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the case-sensitive `If` comparison as why the approved order took the Else branch,
  and the fix (case-insensitive + trimmed comparison) — and did NOT misdiagnose it as a job fault or a
  bad input value.

Playbook: `references/runtime-exceptions/playbooks/if-wrong-branch.md`.
