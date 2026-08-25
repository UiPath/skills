---
confidence: medium
---

# Job Stopped — Unexpected Exit Code (Generic, non-0x40010004)

## Context

A job faults with `Job stopped with an unexpected exit code: <code>` where the code is an **OS/CLR process exit code**, not a UiPath error. These are the executor process's raw exit status — the real fault is upstream (an unhandled exception, a native crash, a session teardown). When an exception escapes to the process boundary with no top-level handler, the job `Info` and error logs can carry only this exit code while the real exception stays in the execution traces. The diagnostic job is to recover the real cause, not stop at the code.

> `0x40010004` (`DBG_TERMINATE_PROCESS`) has its own playbook — the executor was killed externally. See `job-stopped-exit-code-0x40010004.md`. This playbook covers the other codes.

What this looks like:
- `System.Exception: Job stopped with an unexpected exit code: 0xE0434352`
- `... 0xC0000005`
- `... 0xC000026B`
- `... 0x00000001` / `... 0xFFFFFFFF` / `... 0x00000033`
- Job state Faulted; the workflow's own logs may stop abruptly with no handled-exception entry
- The job `Info`/error logs may carry only the exit code when no top-level handler logged the exception before the process exited

Code → meaning (map the code first):
- **`0xE0434352`** — CLR unhandled exception (`.NET` managed exception escaped to the process boundary). The real fault is an unhandled exception inside the workflow. **Most common.**
- **`0xC0000005`** — `STATUS_ACCESS_VIOLATION`; a native component crashed (Excel/Office COM interop, a native UIAutomation/driver, an unmanaged library). Not a managed exception.
- **`0xC000026B`** — `STATUS_DLL_INIT_FAILED_LOGOFF`; the process was terminated during Windows logoff/shutdown — the session ended under the job (cross-reference session-teardown / RDP-drop).
- **`0x00000001` / `0xFFFFFFFF` / `0x00000033`** — generic non-zero process exit; the executor died without a clean UiPath fault. Carries little signal by itself — recover the real error from traces/logs.

What can cause it:
- An unhandled exception in the workflow (no Try/Catch at the top level) — surfaces as `0xE0434352`
- A native crash in a COM/UIAutomation/driver component — `0xC0000005`
- The Windows session ending mid-run (logoff, shutdown, RDP drop) — `0xC000026B`
- Any of the above escaping to the process boundary with no top-level handler, so only the exit code is logged and the exception detail is left in traces

## Investigation

1. Get the failing job and read the exact code from `Info`:
   `uip or jobs get <job-key> --output json` — extract the `0x...` code and map it above. Note `RuntimeType`, `HostMachineName`, `StartTime`/`EndTime`.
2. Recover the **real** error — do not stop at the code. Pull job traces (the executor records the underlying activity/exception even when the job surfaces only the OS code):
   `uip or jobs traces <job-key> --output json` — look for the last executed activity and any exception detail (e.g. `NullReferenceException`, `KeyNotFoundException`, a COM `HRESULT`). Redirect to a file and read back only the error/activity entries.
3. Read error logs for a managed stack trace that preceded the exit:
   `uip or jobs logs <job-key> --level Error --output json`.
4. Confirm the host Robot is on a supported/current version to rule out a known robot-build defect (general hygiene):
   correlate `HostMachineName` with `uip or machines list --output json`. The exit code is produced by the unhandled exception itself, not the robot version — do not expect a version bump to reveal the exception; recover it from traces (step 2).
5. For `0xC000026B`: check `uip or jobs history <job-key>` and the host for a logoff/shutdown at the failure timestamp (session teardown, not a workflow bug).

## Resolution

- **`0xE0434352` (unhandled .NET exception) — primary path:** the code is a symptom; fix the underlying unhandled exception surfaced in step 2/3. Add top-level exception handling (Global Exception Handler or a top-level Try/Catch) so the real error is logged instead of collapsing to an OS code.
- **`0xC0000005` (access violation):** a native component crashed — identify it from the last activity in traces (commonly Excel/Office COM interop or a UIAutomation driver). Update the offending activity package / Office / driver, ensure the interop dependency is installed on the host, and prefer non-COM alternatives where available.
- **`0xC000026B` (terminated during logoff):** the session ended under the job — keep the unattended session stable (do not log off the target user while jobs are scheduled; use Login to Console / a dedicated unattended user). Rerun. If it recurs, treat as a session-stability problem, not a workflow bug.
- **`0x00000001` / `0xFFFFFFFF` / `0x00000033` (generic non-zero exit):** these carry little signal alone. Recover the real error from traces/logs (step 2/3); if none is captured, **add a Global Exception Handler / top-level Try-Catch** so the next run logs the exception type and stack instead of collapsing to the raw code, then rerun and diagnose the exception it reports.

Prevention:
- Ship a Global Exception Handler so unhandled exceptions are logged with a stack trace instead of collapsing to an OS code.
- Keep robots on a current, supported version as general fleet hygiene.
- Keep host prerequisites (Office/COM, drivers) patched to avoid native crashes.
