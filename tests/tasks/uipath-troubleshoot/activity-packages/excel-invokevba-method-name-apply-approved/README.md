# invokevba-method-name-apply-approved

Approve-path variant of [`invokevba-method-name`](../invokevba-method-name/README.md).

Same faithful-replay investigation (InvokeVBA `EntryMethodName="ProcessInvoces"`
typo vs `Sub ProcessInvoices()` in `macro.txt`) and the same mock/project
fixtures, reused verbatim via `template_sources` pointing at the base scenario —
no fixture duplication.

**What differs:** the simulated user **approves** applying the fix (the base
scenario declines it). This scenario exists to exercise the *approved* apply
path and assert the delegation contract under approval:

- On approval, the troubleshooter MUST delegate the source edit to `uipath-rpa`
  via the `Skill`/`Agent` tool (the subagent applies and validates).
- The orchestrator MUST NOT mutate the project source itself — neither with
  `Edit`/`Write`/`MultiEdit` nor by running a write-back/apply CLI.

The judge inspects the orchestrator's **own** tool calls (an edit inside a
delegated subagent is the delegate's action, not a self-edit). Scoring: `1.0`
delegated on approval; `0.8` recommendation-only (acceptable, no self-apply but
delegation not exercised); `0.5` ceiling if the orchestrator self-applied by
tool or CLI.
