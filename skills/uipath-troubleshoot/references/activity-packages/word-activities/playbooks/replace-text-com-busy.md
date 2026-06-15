---
confidence: medium
---

# Replace Text in Document — "Application is busy" / COM Interop Retry Failure (0x8001010A)

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` (`UiPath.Word.Activities.ReplaceTextInDocument` modern, `UiPath.Word.Activities.WordReplaceText` classic) faults with a COM HRESULT
- Error message contains one of:
  - `The message filter indicated that the application is busy. (Exception from HRESULT: 0x8001010A (RPC_E_SERVERCALL_RETRYLATER))`
  - `Call was rejected by callee. (Exception from HRESULT: 0x80010001 (RPC_E_CALL_REJECTED))`
- Often intermittent — the same workflow succeeds on one run and faults on the next

What can cause it:
- Microsoft Word (WINWORD.EXE) is **busy or unresponsive** when the activity issues its COM call: another WINWORD.EXE is open in the background, the document is locked by another user/session, or Word is stalled on a modal pop-up dialog
- When the surrounding scope runs with `Visible = False`, a blocking dialog is invisible but still wedges the COM call

What to look for:
- Extra WINWORD.EXE instances in Task Manager on the robot host.
- Whether the document is also open in an interactive desktop window.

## Investigation

1. Capture the exact HRESULT (`0x8001010A` / `0x80010001`) and confirm the faulted activity is `Replace Text in Document` / `Replace Text` inside a `Word Application Scope` / `Use Word File` container.
2. Ask the user (or someone with desktop access on the robot host, signed in as the robot's Windows user) to check for orphaned WINWORD.EXE processes and whether the target document is open in another window.
3. Re-run with the scope `Visible = True` and observe whether Word shows a blocking dialog (recovery sidebar, macro/trust prompt, license activation) during the run.

## Resolution

- **If a stray / orphaned WINWORD.EXE is holding Word busy** — add a `Kill Process` activity with `ProcessName = "WINWORD"` immediately **before** the Word scope to clear locked sessions, and ensure the scope disposes so Word always closes cleanly. Confirm the file is not open in another desktop window during the run.
- **If a modal dialog is blocking** — surface it by running `Visible = True`, then clear the source (open the document once to dismiss a recovery/trust prompt, complete Office activation under the robot user, add the folder to Trusted Locations). See [word-scope-hangs-background-prompt.md](./word-scope-hangs-background-prompt.md) for the dialog-by-dialog breakdown.
- **If the document is locked by another process** — stop the concurrent accessor (a second job, a sync/AV client, an interactive session); see [word-scope-file-corrupted.md](./word-scope-file-corrupted.md) for the lock-clearing steps.
- **As a resilience guard** — wrap the operation in a `Retry Scope` so a transient `RPC_E_SERVERCALL_RETRYLATER` retries rather than faulting the job on the first busy signal.
