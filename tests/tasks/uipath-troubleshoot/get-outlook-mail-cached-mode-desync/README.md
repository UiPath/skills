# Get Outlook Mail Messages - Cached Exchange Mode Desync (Branch 5)

This scenario reproduces the **silent-miss** signature of the
`Get Outlook Mail Messages` failures playbook: a job that reports
**Success with no error** while the activity quietly returns only a
fraction of the Inbox. Recent emails the user can see in the Outlook
desktop client never make it into the export, and nothing in Orchestrator
flags a problem.

## What this scenario uncovers

**Root Cause:** The Robot's Outlook account runs in **Cached Exchange
Mode** with a **restricted Offline Settings window** ("Mail to keep
offline" set to a few months). Mail outside that window is never synced
into the local `.ost` cache. `Get Outlook Mail Messages` reads Outlook's
**local store** through COM, so it can only return cached mail - it cannot
see items the full online client shows. The job ends Successful, the
activity returns the cached subset, and the shortfall is invisible unless
you compare the retrieved count to the real Inbox size.

The tell is in the full job logs:
`[Get Outlook Mail Messages] retrieved 142 messages from 'Inbox'
(Top=500, no filter); oldest item dated 2026-03-03` - the oldest returned
item sits at a ~3-month cache cutoff while `Top` is high and no `Filter`
narrows the result.

This maps to:
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
(**Branch 5 - Cached Exchange Mode desync**).

The user is framed as **off-host**, so the correct agent behavior is to
diagnose from Orchestrator + the workflow source, then hand the user a
host-side check (inspect/widen the Offline Settings slider to All, or
disable Cached Exchange Mode, and re-run; optionally move to Graph
o365-activities) **without fabricating host actions** - Cached Exchange
Mode state is only verifiable on the host.

## Sibling-branch comparison (why this is Branch 5, not 1-4)

| Branch | Signature | This scenario? |
|--------|-----------|----------------|
| **B1** Folder not resolved | `The specified folder does not exist` (nested/localized/shared-mailbox path) | No - job log shows `Inbox` resolved on the default account |
| **B2** Timeout on volume | `The operation has timed out` after `TimeoutMS`; job **Faulted** | No - job ended **Successful** in ~6 s |
| **B3** Outlook not running / COM | `The Outlook application is not running` / COM cast / hang | No - Outlook attached, read completed cleanly |
| **B4** Malformed `Filter` | `Filter` error, or zero results with a `Filter` set | No - **no `Filter`** is set; result is partial, not zero |
| **B5** Cached Exchange Mode desync | **No error**, but recent/older mail visible in the client is missing | **Yes** - this scenario |

The defining trait of B5 is the **absence** of an error. The job is
`Successful`, the error-level logs are empty, and the only signal is the
shortfall + the oldest-item-at-cache-cutoff line in the full logs. An
agent that latches onto "Top too low" or "add a Filter" has misread the
case: `Top=500` is high and there is no Filter to fix - the limitation is
the host's cache window, not the workflow.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: `Get Outlook Mail Messages` with `MailFolder="Inbox"`, `Top="500"`, no `Filter` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the Branch 5 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table (quoted + unquoted UUID variants) |

The job discovery is modeled for a **SUCCESS-state** case:
`or jobs list ... --state Faulted` returns an **empty** list, while the
no-state and `--state Successful` variants return the one Successful job.
`or jobs get` reports a benign success `Info`; `or jobs logs ... --level
Error` is empty; the full `or jobs logs` carries the shortfall signal.

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

The judge **scores the conclusion, not the trajectory.** It grades the
agent's final response and its tool calls (did it Read the
mail-activities playbook), not internal investigation state.

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `get-outlook-mail-failures.md` Branch 5 (Cached Exchange
  Mode desync).
- Agent recognized the **silent miss** (Successful, no error, fewer
  messages than exist), **ruled out** the workflow-side causes (`Top`
  high, no `Filter`, correct folder), and attributed the shortfall to
  Cached Exchange Mode / a restricted Offline Settings window.
- Agent handed a **host-side check** (widen the Offline Settings slider to
  All / disable Cached Exchange Mode and re-run; optionally move to Graph
  o365-activities) **without fabricating host actions**.
