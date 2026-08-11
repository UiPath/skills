# Send Outlook Mail Message Failure - NullReferenceException (uninitialized To)

This scenario reproduces a runtime `Send Outlook Mail Message` failure
caused by an **uninitialized input**: the activity's `To` field is bound
to a variable (`recipient`) that an upstream step never assigned, so it
is `Nothing`/null at runtime. The activity dereferences the null and
faults with
`System.NullReferenceException: Object reference not set to an instance
of an object`.

## What this scenario uncovers

**Root Cause:** In `Main.xaml`, `Send Outlook Mail Message` binds
`To="[recipient]"`. The `recipient` variable is declared on the Main
Sequence but is never assigned (the config read that should populate it
is missing), so `To` is null. The activity raises
`NullReferenceException` at `SendOutlookMail`. The empty input is
visible in the job-log Trace just before the fault:
`To='' (empty); Subject='Welcome'`.

This maps to:
`references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
(Branch 3 - Uninitialized input).

The fix is a **workflow bug fixable in Studio** - initialize/populate
`recipient` (and guard the inputs) before the Send, validate by
hardcoding a literal address. It is NOT a host-side fix.

## Sibling-branch comparison

The Send Outlook Mail playbook has three cause-branches. Each has its
own scenario so the agent must discriminate on the error signature, not
just match the activity name.

| Branch | Scenario | Signature | Surface | Fix location |
|--------|----------|-----------|---------|--------------|
| 1 - COM cast / library not registered | `send-outlook-mail-com-not-registered` | `InvalidCastException` / `COMException` (`REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED`) | COM layer (Outlook install / bitness) | Host (install/repair Outlook, match bitness) |
| 2 - Timeout / hang | `send-outlook-mail-timeout-security-prompt` | Timeout / hang, no clean inner exception | Session / UI (security prompt, Work Offline) | Host (suppress prompt, go Online, raise TimeoutMS for true slowness) |
| **3 - Uninitialized input (this scenario)** | `send-outlook-mail-null-input` | `NullReferenceException` at the activity | Inputs (null `To`/`Subject`/`Body`) | **Workflow / Studio** (populate the variable, guard inputs) |

The reject list in the LLM judge rejects any answer that lands on
Branch 1 or Branch 2, on a generic SMTP/network/credentials error, on
an invalid-recipient ("mailbox does not exist") read of the empty
address, or on a host-side fix.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `To="[recipient]"` with `recipient` declared but never assigned in `Main.xaml` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table (quoted + unquoted arg variants) |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature (Branch 3) rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This test **scores the conclusion, not the trajectory.** The two
required criteria are `skill_triggered` (the `uipath-troubleshoot` skill
activated) and an `llm_judge` graded against `RESOLUTION.md`. The judge
reads only the agent's presented final response and its tool calls - it
does not inspect `.local/investigations/` internal state. An agent that
reaches the right root cause via a different command path still passes.

The agent passes when it:

- invoked the `uipath-troubleshoot` skill;
- matched `send-outlook-mail-failures.md` Branch 3 (uninitialized input);
- named the `NullReferenceException` at the Send Outlook Mail Message
  activity and attributed it to the uninitialized `recipient` variable
  bound to `To` (empty/null input), citing `Main.xaml` and/or the
  empty-To job-log Trace;
- recommended a **workflow** fix (initialize/populate `recipient`, guard
  the inputs, validate by hardcoding a literal address) - not a
  host-side fix.
