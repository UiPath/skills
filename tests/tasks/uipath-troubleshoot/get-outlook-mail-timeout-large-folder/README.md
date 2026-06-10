# Get Outlook Mail Messages Failure - Timeout on a Large Folder

This scenario reproduces a runtime `Get Outlook Mail Messages` fault
caused by **message volume vs the timeout window**: the activity reads
the `Archive` folder (approx. 18,420 items) with `Top="5000"` and
`OnlyUnreadMessages="False"`, leaving the default `TimeoutMS="30000"`.
Enumerating that many messages cannot complete inside 30 seconds, so the
activity raises
`System.TimeoutException: The operation has timed out.`

## What this scenario uncovers

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml`
asks for up to 5,000 messages from a folder of ~18,420 items with no
unread-only filter, against a 30-second `TimeoutMS`. The read cannot
finish in the window, so the job faults at the full 30s boundary. The
`MailFolder` string, the `Account`, and the Outlook/COM session are all
fine - this is a volume-vs-timeout problem.

This maps to:
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
(Branch 2 - Timeout on a large folder).

The correct fix raises `TimeoutMS` (e.g. 60000+) **and** reduces the batch
(`Top` ~10-20, enable `OnlyUnreadMessages`, or add a `Filter`); for a
chronically huge folder, migrate to the Graph o365-activities.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: `Get Outlook Mail Messages` on `Archive` with `Top="5000"`, `OnlyUnreadMessages="False"`, `TimeoutMS="30000"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The smoking gun is in the full job logs
(`or-jobs-logs-b0c1d2e3-output-json.json`): an Info line that the
`Archive` folder holds `approx. 18,420 items; Top=5000,
OnlyUnreadMessages=False`, a Warn at +25s that enumeration was still
running as the 30s timeout approached, then the timeout Error - steering
the diagnosis toward volume vs `TimeoutMS` rather than a folder or COM
fault.

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Sibling-branch comparison

| Branch | Signature | Why this scenario is NOT it |
|---|---|---|
| 1 - Folder not resolved | `The specified folder does not exist` | Error is a timeout; the folder enumerated and returned 4,100 items |
| **2 - Timeout on a large folder** | **`The operation has timed out` after `TimeoutMS`** | **This scenario** - ~18k items, `Top=5000`, default 30s |
| 3 - Outlook not running / COM / privilege | `Outlook is not running` / COM cast / freeze | Outlook responded and returned items; no COM/privilege error |
| 4 - Malformed `Filter` | `Filter` error or zero results with a filter set | No `Filter` is configured on the activity |
| 5 - Cached Exchange Mode desync | **No exception**, mail silently missing | Job hard-faults with a timeout, not a silent miss |

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `get-outlook-mail-failures.md` Branch 2 (timeout on a
  large folder).
- Agent attributed the fault to message volume vs `TimeoutMS` (`Top`
  high/unset, `OnlyUnreadMessages` off) and recommended raising
  `TimeoutMS` **and** reducing the batch (`Top` / `OnlyUnreadMessages` /
  `Filter`).

This scenario **scores the conclusion, not the trajectory**: the
`llm_judge` grades the agent's final response and tool calls against
`RESOLUTION.md`, not any specific path through the investigation or any
internal `.local/investigations/` state.
