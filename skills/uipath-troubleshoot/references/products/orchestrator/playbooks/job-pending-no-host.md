---
confidence: high
---

# Job Pending — No Available Host

## Context

What this looks like:
- Job stuck in Pending state
- Job information shows "No host is available on the machine template assigned for this job"
- Output shows "The job hasn't finished yet"

What can cause it:
- Host machine's UiPath Assistant is not signed in to Orchestrator
- UiPath Assistant is connected to a different Orchestrator URL or tenant than the one where the job was triggered
- UiPath Robot Service is stopped on the host machine
- Network connectivity lost between host and Orchestrator

What to look for:
- Machine template assigned to the job and which hosts are registered to it
- Connection status of hosts on that machine template (connected vs disconnected)

## Investigation

1. Check the machine template assigned to the pending job and its connected hosts — `uip or machines list --output json`
2. Check the local machine's hostname and compare it against the hosts registered to the machine template to determine if the agent is running on one of the assigned machines
3. If on the assigned machine: check the Robot Service status — `sc query UiRobotSvc`
4. Check whether the Assistant process is running — `tasklist /FI "IMAGENAME eq UiPath.Assistant.exe"`
5. If the service is running, verify the Assistant is connected to the same Orchestrator URL and tenant where the job is pending
6. If NOT on the assigned machine: the job is targeting a different machine — the user needs access to that machine or the job needs to be reassigned

## Resolution

- **If on the assigned machine and Assistant is signed out:** sign in to the Assistant and connect to the Orchestrator URL
- **If on the assigned machine and Assistant is connected to the wrong Orchestrator/tenant:** update the connection in Assistant preferences to point to the correct Orchestrator URL and tenant
- **If on the assigned machine and Robot Service is stopped:** restart the UiPath Robot Service
- **If on the assigned machine and network issue:** verify the host can reach the Orchestrator URL, check firewall/proxy settings
- **If not on the assigned machine:** either connect to the assigned machine and restore Assistant connectivity, or reassign the job to a machine template that includes the current machine
