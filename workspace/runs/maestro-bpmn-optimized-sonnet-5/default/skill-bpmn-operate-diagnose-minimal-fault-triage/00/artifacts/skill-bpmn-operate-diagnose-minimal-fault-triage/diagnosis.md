# Diagnosis: job-triage-001 / inst-triage-001 (folder-public)

## Faulting BPMN element
`Task_InvokeLegacyRpa` (service task, `Orchestrator.StartJob` extension) — confirmed by incident `inc-triage-001`, element-executions, and cursors (state: `Faulted`). The prior `Start_Manual` start event completed normally.

## User-visible symptom
The run stalled/failed immediately after start with runtime variable `triageStatus = PendingChildProcess` never advancing. The instance recorded a single incident of category `BindingResolution`: *"Resource binding 'folderPath' resolved to a folder the process cannot access."*

## Likely root cause
The deployed BPMN asset shows `Task_InvokeLegacyRpa` binds its `folderPath` input via `=bindings.LegacyRpaFolder`. This root binding resolves successfully (it is not missing or malformed) but points to an Orchestrator folder that the executing process/service account does not have access rights to. The BPMN expression itself and the element structure are correct — this is an access/permissions problem on the resolved target folder, not a malformed binding reference or a stale generated artifact.

## Ownership of the fix
**Cloud configuration** — the folder access rights/permissions for the account running this job against the folder referenced by the `LegacyRpaFolder` binding need to be granted or corrected in the tenant/Orchestrator environment.

(Not `BPMN source`: the binding expression and service task are well-formed. Not `Generated package metadata`: the binding resource resolved, it just points at a folder lacking access — no evidence of a missing/stale `bindings_v2.json` entry. Not `Integration Service enrichment`: this is an `Orchestrator.StartJob` binding resolution issue, not an unresolved IS connector/connection binding.)

## Safe next operate action
Do not retry, cancel, or migrate this instance yet. First have someone with tenant admin access verify and, if needed, grant folder access permissions for the process's running identity on the folder that `LegacyRpaFolder` resolves to. Once folder access is confirmed correct in the cloud configuration, the instance can be considered for a retry as a separate, explicitly consented action.
