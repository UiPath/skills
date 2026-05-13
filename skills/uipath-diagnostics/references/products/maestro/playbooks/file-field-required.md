---
confidence: high
---

# 'File' Field Required — DAP-RT-1003 (502)

## Context

What this looks like:
- HTTP 502 surfaced by Maestro
- Error message: `The "File" field is required. Error code: DAP-RT-1003.`
- Always raised by an Integration Service activity that expects a file input (typically Document Understanding or GenAI activities)

What can cause it:
- The `File` input on the activity is unmapped or mapped to a variable that is `null`/empty at runtime
- The upstream activity that should have produced the file failed silently and left the file variable unset
- File was previously linked to an Orchestrator job whose retention expired (orphaned attachment — see [attachment-not-found](attachment-not-found.md))
- File variable defined as a process variable instead of an argument, breaking the binding in deployed mode

What to look for:
- The activity's `elementId` from the incident → confirm it's a DU/GenAI step
- Variables API: is the file variable `null`?
- The upstream activity's status — did it actually produce a file?

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json` — incident `elementId` identifies the failing activity
2. Pull the variables for that element: `uip maestro instance variables <instance-id> -f <folder-key> --parent-element-id <element-id> --output json` — confirm the file variable is null
3. Trace upstream element executions to see where the file should have been produced: `uip maestro instance element-executions <instance-id> -f <folder-key> --output json`
4. If the file came from a previous job, check whether job retention has elapsed (see [attachment-not-found](attachment-not-found.md))

## Resolution

- **If unmapped input:** map the activity's `File` input to a non-null variable in the BPMN task's input mapping
- **If upstream failure:** fix the upstream activity that should have populated the file; add a boundary error event or a null check before the DU/GenAI step
- **If null on optional path:** add an exclusive gateway before the DU/GenAI step that skips it when the file is null
- **If attachment orphaned by retention:** redesign so files come from a stable source (Data Fabric, storage bucket) rather than from a job attachment — see [attachment-not-found](attachment-not-found.md)
- **If file modeled as a variable:** convert it to an argument so binding resolution works in deployed mode

## References

- [Docs: About Integration Service Activities](https://docs.uipath.com/activities/other/latest/integration-service/about-the-integration-service-activities)
