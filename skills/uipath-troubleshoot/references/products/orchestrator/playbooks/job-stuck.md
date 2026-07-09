---
confidence: low
---

# Job Stuck in Running

## Context

A job remains in Running state indefinitely with no progress visible in traces.

What this looks like:
- Job shows Running state for an unusually long time
- No progress visible in job traces
- Robot may still appear as Busy

What can cause it:
- Robot service not running or unresponsive on the host machine
- Process waiting for user input (attended) with no visible Assistant dialog
- BPMN/Agentic Process (ProcessOrchestration runtime) — these have different stuck patterns than standard jobs
- For ProcessOrchestration jobs: the job may be serverless (no robot/machine). If HostMachineName is empty, heartbeat detection and robot-level timeouts don't apply
- Debug run with redirected folder bindings changing execution context
- Child service task stuck waiting for completion

What to look for:
- Check job traces for the last activity that executed
- Check if the process is ProcessOrchestration runtime — look for empty HostMachineName
- Check if there's a ParentJobKey — if so, query the parent job's state
- Check if a child service task is stuck

## Resolution

- If robot is unresponsive: restart the UiPath Robot Service
- If attended and waiting for input: check the Assistant dialog visibility
- If ProcessOrchestration with stuck child task: investigate the child task
- If debug run: check for debug_overwrites.json in the source project
