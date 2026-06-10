---
confidence: high
---

# Job Pending — No Available Host

## Context

What this looks like:
- Job stuck in Pending state
- Job information shows "No host is available on the machine template assigned for this job"
- Output shows "The job hasn't finished yet"
- The machine template assigned to the job currently has zero connected runtimes (`robotVersions` empty / no signed-in Assistant)

What can cause it:
- Host machine's UiPath Assistant is not signed in to Orchestrator
- UiPath Assistant is connected to a different Orchestrator URL or tenant than the one where the job was triggered
- UiPath Robot Service is stopped on the host machine
- Network connectivity lost between host and Orchestrator
- No host machine is installed on the assigned template at all — the user is on a different machine that is not part of the template's host list, or no host has ever connected to the template (this is the "not on the assigned machine" branch handled by Investigation step 6 and the corresponding Resolution branch below)

What to look for:
- Machine template assigned to the job and which hosts are registered to it
- Connection status of hosts on that machine template (connected vs disconnected)

**Discriminator vs [job-pending-stale-dispatch.md](./job-pending-stale-dispatch.md):** before concluding no-host, check `uip or machines list --all-fields` for the assigned template. If it currently has a connected runtime (`robotVersions` populated) AND credentials/mode are valid AND `JobHistory` contains only the original Pending entry, the host is actually present — the `PendingReasons.Errors` codes are a stale snapshot from the original dispatch attempt. Switch to that playbook; the remediation is to stop and re-trigger, not to provision a host. Two traps that look like no-host but are not: the PendingReasons phrase "…none connected to **this folder**" is the dispatch-time verdict, NOT current proof the template is unassigned (no `uip` command can verify folder→template assignment, so do not confirm that as a cause); and `Used.Unattended == Allowed` is NOT exhaustion when the consumed slot is the connected template's own idle runtime. **Also**: `Job.MachineKey` is empty for *every* Pending job (Orchestrator only populates it when a host accepts the job). MachineKey emptiness is NOT evidence of no-host — it is the normal Pending-state value for both no-host and stale-dispatch — verify host presence via `machines list` (`robotVersions`) instead.

## Investigation

1. Check the machine template assigned to the pending job and its connected hosts — `uip or machines list --output json`
2. Check the local machine's hostname and compare it against the hosts registered to the machine template to determine if the agent is running on one of the assigned machines
3. If on the assigned machine: check the Robot Service status — `sc query UiRobotSvc`
4. Check whether the Assistant process is running — `tasklist /FI "IMAGENAME eq UiPath.Assistant.exe"`
5. If the service is running, verify the Assistant is connected to the same Orchestrator URL and tenant where the job is pending
6. If NOT on the assigned machine: the job is targeting a different machine — the user needs access to that machine or the job needs to be reassigned

## Resolution

- **If no host is connected to the assigned template at all (`robotVersions` empty):** no machine is available to run the job. Connect/sign a robot into a machine on that template (Assistant in Service/Unattended mode, pointed at this Orchestrator URL + tenant), or assign a machine template that has a connected host to the folder. Re-triggering will NOT help while no host is connected — a fresh dispatch finds the same empty template and lands back in Pending.
- **If on the assigned machine and Assistant is signed out:** sign in to the Assistant and connect to the Orchestrator URL
- **If on the assigned machine and Assistant is connected to the wrong Orchestrator/tenant:** update the connection in Assistant preferences to point to the correct Orchestrator URL and tenant
- **If on the assigned machine and Robot Service is stopped:** restart the UiPath Robot Service
- **If on the assigned machine and network issue:** verify the host can reach the Orchestrator URL, check firewall/proxy settings
- **If not on the assigned machine:** either connect to the assigned machine and restore Assistant connectivity, or reassign the job to a machine template that includes the current machine
