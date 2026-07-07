# Send Outlook Mail Message Timeout - Hidden Security Prompt (Branch 2)

This scenario reproduces a runtime `Send Outlook Mail Message` failure
where the activity **times out / hangs**: on an unattended Robot, the
Outlook COM send triggers the Object Model Guard security prompt ("A
program is trying to send an email message on your behalf") which is
foregrounded but invisible and awaiting input. With no one present on
the unattended session to dismiss it, the call blocks until `TimeoutMS`
(30000 ms) and the job faults with
`System.TimeoutException: The operation has timed out.`

## What this scenario uncovers

**Root Cause:** The `SendOutlookMail` activity in `Main.xaml` drives the
Outlook desktop client through COM. On the unattended session (machine
`MOCK-HOST`, account `UIPATH\ROBOTUSER1`) the hidden Object Model Guard
prompt blocks the send until `TimeoutMS` elapses. **Work Offline** on
the Robot's profile is the sibling sub-cause with the same signature.

This maps to:
`references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
-- specifically **Branch 2 ("Activity times out or hangs")**.

The user is framed as **off-host**, so the correct agent behavior is to
hand a host-side check list (ensure a profile exists, turn off Work
Offline, register AV with Windows Security Center or set the
programmatic-access GPO, and/or switch to SMTP/Graph for unattended)
rather than try host commands itself. The real fix is **host-side
and/or design** -- NOT merely raising `TimeoutMS`.

## Sibling-branch comparison (same playbook, different branch)

| Branch | Signature | Cause | This scenario? |
|---|---|---|---|
| Branch 1 -- COM cast / library not registered | `InvalidCastException` / `COMException` `REGDB_E_CLASSNOTREG` / `TYPE_E_LIBNOTREGISTERED` | Outlook not installed, bitness mismatch, corrupt type library, orphaned `OUTLOOK.EXE` | No -- Outlook launched + profile loaded; clean timeout, no cast error |
| **Branch 2 -- Activity times out or hangs** | **timeout / hang, `System.TimeoutException`** | **hidden Object Model Guard security prompt or Work Offline on an unattended session; slow first profile load** | **Yes** |
| Branch 3 -- Uninitialized input | `NullReferenceException` at the activity | `To`/`Subject`/`Body` or attachment path is null | No -- inputs are literals in `Main.xaml` |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `SendOutlookMail` with literal `To`/`Subject`/`Body` and `TimeoutMS="30000"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The smoking-gun is in the full job-logs fixture
(`or-jobs-logs-b4d5e6f7-output-json.json`): Info shows Outlook launched
and the profile loaded, then a **Warn** -- "[Send Outlook Mail Message]
Outlook is not responding to the send request; the call has been
pending for >25s (an interactive prompt may be awaiting input on a
non-interactive session)" -- then the timeout Error at exactly
`TimeoutMS`. This steers toward the hidden prompt on the unattended
session without naming it as the answer.

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This scenario **scores the conclusion, not the trajectory.** The
`llm_judge` grades the agent's final response and tool calls against
`RESOLUTION.md`; it does not require a specific investigation path or
internal `.local/investigations/` state.

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `send-outlook-mail-failures.md` Branch 2 (timeout/hang),
  not Branch 1 (COM cast) or Branch 3 (null input).
- Agent attributed the hang to a hidden Outlook security prompt (Object
  Model Guard) -- or Work Offline -- on the unattended session.
- Agent handed a host-side check list (profile, Work Offline, AV /
  Security-Center registration or programmatic-access GPO, and/or
  SMTP/Graph for unattended) and did **not** recommend merely raising
  `TimeoutMS`, nor fabricate host commands it could not run.
