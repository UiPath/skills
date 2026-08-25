---
confidence: low
---

# BPMN Job Stuck or No Error Reported

## Context

What this looks like:
- BPMN process instance appears stuck with no progress
- No error reported in Orchestrator job state
- Child jobs may or may not have been created

What can cause it:
- A connection was disconnected during execution — Maestro instances do not propagate faults to Orchestrator job state by default
- ~60-second delay in WaitForOrchestratorJobCompletion — known backend issue where the orchestration layer takes ~60s to resume after receiving a job completion signal
- Parent Maestro instance was cancelled
- Child job was never created — upstream issue with binding resolution, folder mismatch, or missing release

What to look for:
- Check Maestro Instance Management for incidents (may not appear in Orchestrator)
- Check if child jobs were actually created
- Check if the parent instance is still active
