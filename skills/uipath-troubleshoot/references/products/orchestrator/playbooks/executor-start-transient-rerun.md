---
confidence: medium
---

# Executor Start / Session — Transient Failure (rerun-class)

## Context

An unattended job faults at (or near) executor start with a **transient session/infrastructure** error — a one-off blip rather than a persistent config, credential, or license fault. Signatures in this class:

```
Job faulted due to service shutdown or disconnect.
Job faulted due to service shutdown.
Could not start executor. Rdp connection failed: Message: The connection transport layer failed., Last error: 131085
Could not start executor. Rdp connection failed: Message: The disconnection was initiated by the user logging off their session on the server. Last error: 65548
Could not start executor. A specified logon session does not exist. It may already have been terminated. (0x80070520)
Could not start executor. User is running another job. Waiting for the job to finish timed out.
The job was transitioned to a faulted state as a result of a cleanup action for jobs in Terminating state.
```

What this looks like:
- Faulted at/near start (or mid-run for the service-shutdown/disconnect case), with a message pointing at a **session/transport/service** event, **not** a Windows logon-failure code, a slot/console message, or a licensing quota.
- Often **intermittent** — earlier and later jobs on the same machine/user succeed.

What causes it (all transient, shared fix = rerun):
- **Robot service shutdown / disconnect** — the Robot service restarted or lost its Orchestrator connection while the job was starting or running.
- **RDP transport drop (`131085`)** — the session's transport layer failed mid-handshake.
- **User logged off the session (`65548`)** — a human logged off the session the robot was using.
- **Stale logon session (`0x80070520`)** — the session Windows was going to use was already terminated.
- **Waiting for prior job timed out** — the user was still running another job and the wait window elapsed.
- **Terminating-state cleanup** — the robot went **offline** while the job was Terminating, so Orchestrator's cleanup transitioned it to Faulted.

What to look for:
- The message matches one of the signatures above and carries **no** persistent-fault marker (no `Logon failed` / `0x000005..` code → not [job-faulted-logon-failure.md](./job-faulted-logon-failure.md); no `Creating user session timed out` → not [job-faulted-session-timeout.md](./job-faulted-session-timeout.md); no `workstation is in use` / `console` → not the slots/console playbooks; no quota message → not [serverless-license-quota.md](./serverless-license-quota.md)).
- **Intermittency** across recent jobs on the same host/user — the strongest signal that it is transient.

## Investigation

1. **Get the faulted job:** `uip or jobs get <job-key> --output json` → capture the exact message and confirm it matches a rerun-class signature (and carries none of the persistent-fault markers above).
2. **Check intermittency:** `uip or jobs list --folder-key <key> --output json` → do other recent jobs on the same machine/user succeed? Mixed success/failure ⇒ transient.
3. **Rule out the persistent siblings** — scan the message for a logon code / session-timeout / slots / console / quota string. If present, route to that specific playbook instead of rerunning.
4. **(Recurring only) note the Robot version** — `uip or machines list --all-fields --output json`; several of these are addressed in newer Robot builds.

## Resolution

- **Rerun the job.** These are transient session/service events; a fresh run on a healthy host typically succeeds.
- **If it recurs on a specific host/version:** update the Robot to the latest version (several of these signatures are fixed in newer builds) and investigate host stability — RDP/network reliability, robot-to-Orchestrator connectivity, and session hygiene (humans logging off sessions the robot uses, service restarts).
- **Terminating-cleanup case:** confirm the robot's connectivity/uptime — the job was cleaned up because the robot went offline; restore the host and rerun.
- **Confirm the signature before a blind rerun.** A persistent logon/credential/license fault will just re-fail — only rerun once the message is confirmed to be in this transient class.
