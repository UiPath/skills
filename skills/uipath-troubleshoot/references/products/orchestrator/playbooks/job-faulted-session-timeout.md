---
confidence: medium
---

# Could Not Start Executor — Creating User Session Timed Out

## Context

An unattended job faults shortly after entering Running because the Robot could not create a Windows session on the target machine within its session-creation timeout. Unlike a logon *rejection*, nothing refused the credential — the session-creation step **hung and timed out**.

What this looks like:
- Job state: Faulted. Duration ≈ the Robot's session-creation timeout (tens of seconds up to ~2 min) — NOT sub-second like a logon rejection.
- Error `Info` / robot log contains: `Could not start executor. Creating user session timed out.`
- Crucially, there is **NO** Windows logon-failure/locked/RDP-refused signature: no `Logon failed for user`, no `account is locked`, no `RDP connection failed`, no `0x0000052E` / `0x00000775` / `0x00000532` / `Last error: 131092`. A pure timeout, not an LSA verdict.
- Often intermittent — a re-run of the same job on the same machine may succeed.

What can cause it (pick the branch from evidence):

1. **Known Robot defect on versions earlier than 23.10** (primary documented cause) — a session-creation defect in the Robot times out even on a healthy host; the fix shipped in the Robot 23.10 release. Fingerprint: the executing Robot's version is **< 23.10** AND the host is otherwise healthy (no resource saturation, interactive logon is not abnormally slow). Confirm the exact fixed version against the KB (see Investigation step 5) — the minor-version threshold can move.
2. **Slow interactive Windows logon on the host** — a heavy roaming/mandatory profile, synchronous GPO processing, logon scripts, or real-time AV scanning delays session creation past the timeout. Fingerprint: Robot version **≥ 23.10**, and interactive logon on the host is observably slow for humans too.
3. **Host resource exhaustion** — CPU/RAM/session saturation on the target machine prevents timely session creation. Fingerprint: host metrics show saturation around the fault time.

What to look for:
- Exact `Info` / robot-log wording — `Creating user session timed out` with NO logon-failed/locked/RDP-failed code (this is what separates it from `job-faulted-logon-failure.md`).
- Job entered **Running** and then Faulted after ~the timeout window (separates it from Pending / no-host).
- The Robot version installed on the executing machine (`machines list` → `robotVersions[].version`).
- Whether the host is healthy — other jobs/users create sessions on the same machine around the same time.

**Discriminator vs [job-faulted-logon-failure.md](./job-faulted-logon-failure.md):** both start with `Could not start executor`. That playbook covers an active LSA **rejection** — a Windows code (`0x000005..`), `Logon failed`, `account is locked`, or `RDP connection failed`. This playbook is the **timeout** case: `Creating user session timed out` with none of those codes. If the log carries a `0x000005..` code or `Logon failed`, route to `job-faulted-logon-failure.md`, not here.

## Investigation

1. **Get the faulted job** — `uip or jobs get <job-key> --output json`. Capture `State`, `Info`, `StartTime`, `EndTime` (duration ≈ session-creation timeout), `HostMachineName`, `RuntimeType`. Confirm `Info` contains `Could not start executor. Creating user session timed out.` and carries **no** logon-failure code.
2. **Get error logs** — `uip or jobs logs <job-key> --level Error --output json`. Confirm the robot-service entry attributes the fault to a session-creation timeout, not an LSA logon rejection.
3. **Confirm it entered Running** — `uip or jobs history <job-key> --output json`. A Pending → Running → Faulted transition rules out the no-host / stuck-Pending playbooks (the job was dispatched and started; session creation is what timed out).
4. **Identify the Robot version on the executing machine** — `uip or machines list --output json` (add `--all-fields` if the version is not in the default projection). Read `robotVersions[].version` for the machine/template that ran the job (correlate on `HostMachineName`).
   - Version **< 23.10** AND host otherwise healthy → **cause 1** (known Robot defect). Stop.
   - Version **≥ 23.10** → the version defect is ruled out; investigate host-side session latency (cause 2) or resource exhaustion (cause 3) from host logs/metrics. These are host evidence outside the `uip` surface — report what the runtime data supports and hand the host checks to the user.
5. **(Optional) Corroborate the known issue** — `uip docsai ask "Could not start executor Creating user session timed out Robot version" --source technical_solution_articles`. Use to confirm the exact fixed Robot version and any documented workaround. An empty KB result is not disconfirming — the version evidence in step 4 is load-bearing.

## Resolution

Map the branch from Investigation to the fix:

- **Cause 1 — Robot version < 23.10:**
  - Upgrade the Robot on the executing machine(s) to **23.10 or later** (the release that fixes the session-creation-timeout defect). Verify the exact fixed version via the KB (Investigation step 5) before committing the target version.
  - Interim mitigation: **re-run the job** — the timeout is intermittent on the affected versions, so a retry often succeeds while the upgrade is scheduled.
  - Prevention: keep unattended Robots on a supported/patched version; standardize the Robot version across the machine template so one stale host cannot reintroduce the defect.
- **Cause 2 — Slow interactive logon:** reduce logon latency on the host — trim the roaming/mandatory profile, make GPO/logon-script processing lighter or asynchronous, exclude the Robot working directories from synchronous AV scanning. Where supported, raise the session-creation timeout to cover a legitimately slow logon.
- **Cause 3 — Host resource exhaustion:** relieve CPU/RAM/session pressure on the target machine (reduce concurrent slots, add capacity, or move the workload) so the session can be created within the timeout.
