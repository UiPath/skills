# Get Outlook Mail Messages Failure - Outlook Not Running / Broken COM Session (Branch 3)

This scenario reproduces a runtime `Get Outlook Mail Messages` failure on
an **unattended** Robot where the desktop Outlook **COM session is not
available**: there is no running `OUTLOOK.EXE` instance for the Robot's
Windows user (and/or UiPath and Outlook run at mismatched privilege
levels). The COM layer surfaces this as
`The Outlook application is not running.` with an inner
`System.Runtime.InteropServices.COMException: The RPC server is
unavailable. (Exception from HRESULT: 0x800706BA)`.

## What this scenario uncovers

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml`
attaches to the desktop Outlook through COM interop, but the job runs
**Unattended** on MOCK-HOST as `UIPATH\ROBOTUSER1` with no interactive
desktop and no running Outlook to attach to (and/or a privilege mismatch
blocking the cross-process call). The `MailFolder="Inbox"` and the (absent)
`Filter` are fine -- the failure is the COM session, not folder
resolution.

This maps to:
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
(**Branch 3 -- Outlook not running / COM session broken / privilege
mismatch**).

The fix is **host-side**, and the user is framed as **off-host** (only
Orchestrator access). The correct agent behavior is to hand a host-side
check list (ensure Outlook running / `Start Process outlook.exe` before
the activity / run UiPath and Outlook at the same privilege level /
migrate the unattended read to the modern Graph o365-activities) **without
fabricating host actions** it cannot perform.

## Sibling-branch comparison (Get Outlook Mail Messages)

| Branch | Signature | Cause | This scenario? |
|---|---|---|---|
| 1 - Folder not resolved | `The specified folder does not exist.` | `MailFolder` / `Account` string is wrong (nested backslash path, shared mailbox, localized name) | No - `MailFolder="Inbox"` resolves |
| 2 - Timeout on large folder | `The operation has timed out` after `TimeoutMS` | Folder too big / attachments huge vs the timeout | No - faulted ~4 s with an explicit COM error, not a timeout |
| **3 - Outlook not running / COM session / privilege** | **`The Outlook application is not running.` / COM cast / RPC server unavailable / freeze** | **No running OUTLOOK.EXE for the Robot user on an unattended host, and/or a UiPath-vs-Outlook privilege mismatch** | **Yes** |
| 4 - Malformed `Filter` | `Filter` error or zero results with a filter set | Unquoted / non-DASL/Jet `Filter` value | No - no `Filter` is set |
| 5 - Cached Exchange Mode desync | **No error**, missing recent/old mail | Offline cache window too narrow | No - the job faulted with a hard error |

> **Distinct from the Send Outlook Mail install surface.** A COM
> **library-not-registered / bitness** cast error
> (`REGDB_E_CLASSNOTREG` / `Unable to cast COM object`) attributed to the
> Outlook **install** is the `send-outlook-mail-failures.md` Branch 1
> surface. Here Outlook **is** installed -- it is simply **not running** /
> blocked by privilege. The scenario keeps these distinct.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: a `Get Outlook Mail Messages` activity with `MailFolder="Inbox"` (valid), unattended `project.json` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 3 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session. The smoking gun is in the full job
> logs: an Info that the run is Unattended with no interactive desktop, and
> a line that no running Outlook instance was found for the Robot's user.

## Success criteria

This test **scores the conclusion, not the trajectory** -- two criteria:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent reached the same conclusion as `RESOLUTION.md` (`llm_judge`,
  presentation-graded): matched `get-outlook-mail-failures` Branch 3, named
  the Outlook-not-running / broken COM session failure, attributed it to no
  running Outlook for the unattended Robot user (and/or a privilege
  mismatch) -- not a folder / filter / timeout / registration issue -- and
  handed a host check list (ensure Outlook running / `Start Process
  outlook.exe` / same privilege level / Graph o365 for unattended) without
  fabricating host actions.
