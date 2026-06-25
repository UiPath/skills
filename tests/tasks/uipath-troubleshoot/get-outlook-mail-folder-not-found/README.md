# Get Outlook Mail Messages Failure - Folder Not Resolved (Branch 1)

This scenario reproduces a runtime `Get Outlook Mail Messages` failure
where the configured `MailFolder` cannot be resolved. The activity is
set to read the nested folder `Inbox\Invoices` using backslash
nested-path syntax, which does not resolve to a real Outlook folder on
the project's Mail-package version (`UiPath.Mail.Activities [1.18.3]`).
The job faults with `The specified folder does not exist.`

## What this scenario uncovers

**Root Cause:** `Main.xaml` configures the `Get Outlook Mail Messages`
activity with `MailFolder="Inbox\Invoices"`. The Outlook COM session is
healthy -- the activity attaches to the running Outlook instance under
the default profile -- but the backslash nested-path string does not
resolve, so the activity raises `The specified folder does not exist.`
The fix is to address the subfolder with the absolute path form
`\\<account>\Inbox\Invoices`, or to target the top-level `Inbox`, or to
set the `Account` field when the subfolder lives under a shared mailbox.

This maps to:
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`
(Branch 1 -- Folder not resolved).

This is a **workflow-fixable configuration bug**: the fix is a property
change in `Main.xaml`, not a host-side action. The user has both
Orchestrator access and the project source, so the agent can diagnose
end-to-end from Orchestrator + the workflow source without host data.

## Sibling-branch comparison

The Get Outlook Mail playbook has five cause-branches. This scenario is
Branch 1. What distinguishes it from the others:

| Branch | Signature | This scenario? | Why not |
|--------|-----------|----------------|---------|
| 1 Folder not resolved | `The specified folder does not exist.` | **YES** | `MailFolder="Inbox\Invoices"` backslash nested path fails to resolve |
| 2 Timeout on large folder | `The operation has timed out` after `TimeoutMS` | No | Job ran ~2s; error is folder-not-found, not a timeout; enumeration never started |
| 3 Outlook not running / COM / privilege | `The Outlook application is not running` / COM cast / a freeze | No | Logs show a clean attach to the running Outlook instance; no COM error, no hang |
| 4 Malformed `Filter` | `Filter` error or zero-results-with-a-filter | No | No `Filter` is set; error is folder resolution, not DASL/Jet syntax |
| 5 Cached Exchange Mode desync | No error, but mail visible in the client is missing | No | The job faults with an explicit exception; this is not a silent miss |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with `MailFolder="Inbox\Invoices"` on the Get Outlook Mail Messages activity |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 1 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook Branch 1 signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

This scenario **scores the conclusion, not the trajectory.** The
`llm_judge` grades only the agent's final response and tool calls
against `RESOLUTION.md`; it does not inspect internal investigation
state. Passing requires:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `get-outlook-mail-failures.md` Branch 1 (folder not
  resolved).
- Agent attributed the fault to the `MailFolder="Inbox\Invoices"`
  backslash nested-path string that does not resolve (not a timeout,
  COM/Outlook-not-running, `Filter`, or Cached Exchange Mode cause).
- Agent recommended the absolute-path form
  (`\\<account>\Inbox\Invoices`), or targeting the top-level folder, or
  setting `Account` for a shared mailbox.
