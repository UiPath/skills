# Send Outlook Mail Message Failure - COM Cast / Library Not Registered (Branch 1)

This scenario reproduces a runtime `Send Outlook Mail Message`
(`SendOutlookMail`, `UiPath.Mail.Outlook.Activities`) failure at the
**COM layer**: the activity cannot bind the Outlook COM server and
faults with
`System.InvalidCastException: Unable to cast COM object of type
'Microsoft.Office.Interop.Outlook.ApplicationClass' to interface type
'Microsoft.Office.Interop.Outlook._Application'` and an inner
`COMException: Library not registered. (Exception from HRESULT:
0x8002801D (TYPE_E_LIBNOTREGISTERED))`.

## What this scenario uncovers

**Root Cause:** A process-vs-Outlook **bitness mismatch** (the Robot
executor process is 64-bit - `project.json` `targetFramework: "Windows"`
- against a 32-bit desktop Outlook on MOCK-HOST), or a **corrupted
Office registration / type library**. The `Send Outlook Mail Message`
activity drives the local Outlook desktop application through COM; the
bind fails before any message is composed. The `To` / `Subject` /
`Body` inputs are valid literals and are not the cause.

This maps to:
`references/activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md`
(Branch 1 - COM cast / library not registered).

The user is framed as **off-host** (Orchestrator access only), so the
correct agent behavior is to diagnose from Orchestrator and hand the
user a **host-side check list** (matching-bitness desktop Outlook,
Office Quick Repair, clear orphaned `OUTLOOK.EXE`, optionally migrate
to Send SMTP Mail Message / Microsoft Graph o365 activities) rather
than claim to have run host commands itself.

## Sibling-branch comparison

The Send Outlook Mail Message playbook has three cause-branches. This
scenario exercises Branch 1; the judge rejects the other two.

| Branch | Signature | Cause | This scenario |
|---|---|---|---|
| **1 (this)** | `InvalidCastException` to `_Application` / `COMException: Library not registered` (0x8002801D `TYPE_E_LIBNOTREGISTERED`, `REGDB_E_CLASSNOTREG`) | Outlook not installed / bitness mismatch / corrupted Office registration / orphaned `OUTLOOK.EXE` on the host | **Yes** - 64-bit process vs 32-bit Outlook; host-side fix |
| 2 | Activity times out (`TimeoutMS` elapsed) or job hangs with no exception | Hidden Outlook security prompt, Work Offline, or slow profile load | No - rejected (no timeout/hang; fails fast with a cast) |
| 3 | `NullReferenceException` at the activity | Uninitialized `To`/`Subject`/`Body` or empty attachment path | No - rejected (inputs are valid literals) |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: a `SendOutlookMail` activity with valid literal inputs, `targetFramework "Windows"` (64-bit), dependency `UiPath.Mail.Activities [1.18.3]` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the Branch 1 playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table (`or folders list`, `or jobs list --state Faulted`, `or jobs get`, `or jobs logs --level Error`, `or jobs logs`, plus `docsai ask` passthrough) |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This test **scores the conclusion, not the trajectory.** The
`llm_judge` grades the agent's final response and tool calls against
`RESOLUTION.md`; it does not require any specific investigation path or
internal-state file.

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `send-outlook-mail-failures.md` Branch 1 (COM cast /
  library not registered).
- Agent attributed the failure to the Outlook COM registration /
  bitness mismatch on the host and handed the user a host-side check
  list (matching-bitness Outlook, Office Quick Repair, clear orphaned
  `OUTLOOK.EXE`; optionally SMTP/Graph fallback) without fabricating
  host actions it could not run.
