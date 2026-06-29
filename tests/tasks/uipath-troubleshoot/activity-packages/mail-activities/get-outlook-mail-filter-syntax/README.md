# Get Outlook Mail Messages Failure - Malformed Filter (DASL/Jet)

This scenario reproduces a runtime `Get Outlook Mail Messages` failure caused
by a malformed DASL/Jet `Filter`. The `Filter` property holds
`[Subject] = VarSubject` -- the right-hand value is **unquoted**, so it is not
a valid DASL literal. When Outlook applies the restriction it cannot parse the
condition and the job faults with
`Cannot parse condition. Error at "VarSubject".`, surfaced through COM as
`0x80020009 (DISP_E_EXCEPTION)`. The folder resolves and the COM session is
fine -- the only fault is the filter syntax.

## What this scenario uncovers

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml` runs
with `Filter="[Subject] = VarSubject"`. The value is unquoted, so Outlook's
DASL/Jet parser rejects the condition. The fix is to single-quote the value:
`[Subject] = 'Text to find'`, or with a variable
`"[Subject] = '" + mySubjectVariable + "'"`.

This maps to
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`,
**Branch 4 (Malformed `Filter`)**.

The job logs are the smoking gun: Outlook attaches over COM and the `Inbox`
folder resolves cleanly, then the activity echoes the applied restriction
`[Get Outlook Mail Messages] applying Filter: [Subject] = VarSubject` on the
line immediately before the parse error -- the unquoted value is visible.

## Sibling-branch comparison

This is Branch 4. The agent must NOT conclude any sibling branch (nor a null
variable):

| Branch | Signature | Why it is NOT this scenario |
|---|---|---|
| 1 - Folder not resolved | `The specified folder does not exist` | Log shows `Inbox` resolved on the default profile |
| 2 - Timeout on large folder | `The operation has timed out` after `TimeoutMS` | Faulted in ~2 s with a parse error, not a timeout |
| 3 - Outlook not running / COM / privilege | `The Outlook application is not running` / cast failure / hang | Log shows Outlook attached over COM; no cast error, no hang |
| **4 - Malformed `Filter`** | `Cannot parse condition. Error at "..."` | **This scenario:** unquoted DASL value `[Subject] = VarSubject` |
| 5 - Cached Exchange Mode desync | NO error, mail silently missing | The job faulted with an explicit parse error |
| (not a branch) Null/empty subject variable | n/a | The bug is the missing quotes (DASL syntax), not a null value |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with `Filter="[Subject] = VarSubject"` on the Get Outlook Mail Messages activity |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 4 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This scenario **scores the conclusion, not the trajectory.** The `llm_judge`
grades the agent's final response and tool calls against `RESOLUTION.md`; it
does not require a specific investigation path or any internal-state file.

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the `get-outlook-mail-failures` playbook, Branch 4.
- Agent attributed the fault to the unquoted value in the `Filter`
  expression (`[Subject] = VarSubject`), citing `Main.xaml` and the job-log
  applied-filter line.
- Agent recommended single-quoting the DASL value
  (`[Subject] = 'Text'` / `"[Subject] = '" + var + "'"`) and did NOT conclude a
  sibling branch or a null/empty subject variable.
