---
confidence: high
---

# Missing Value for Required Parameter (400)

## Context

What this looks like:
- HTTP 400 at activity execution
- Error message: `Missing value for required parameter 'id'` (or `'worksheetID'`, `'modelName'`, etc.)
- Often appears immediately after an Integration Service connector update or a Maestro release

What can cause it:
- An API call has a URL template `{id}` placeholder that wasn't substituted
- A required input argument named in the schema was not included in the payload
- Maestro UI is missing a property that exists in Studio/Studio Web (UI bug) — user can't set the value because the field isn't shown
- A connector or activity update added a new required property (e.g., GenAI `modelName`), breaking already-published workflows
- Input argument JSON exceeded the 10,000-character limit and got truncated, dropping the parameter

What to look for:
- Match the missing parameter name from the error to the activity's expected inputs
- Compare actual inputs (Variables API) vs `inputDefinitions`
- Whether the workflow worked before a recent connector/Maestro release

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json` — error message names the missing parameter
2. Pull the activity inputs: `uip maestro <type> instance variables <instance-id> -f <folder-key> --output json`
3. Compare to the activity's `inputDefinitions` in the BPMN/`.bpmn` asset: `uip maestro <type> instance asset <instance-id> -f <folder-key> --output json`
4. Check the Maestro UI for the failing activity — is the missing field even visible? If not, suspect a Maestro frontend bug
5. Verify the input JSON size — over 10,000 characters indicates truncation

## Resolution

- **If parameter genuinely missing:** add it to the activity's input mapping
- **If URL `{id}` placeholder:** ensure the ID value is substituted, not the literal placeholder
- **If Maestro UI doesn't expose the field:** workaround — manually edit the `.bpmn` to add the property, or wait for the FE fix
- **If new required property from connector update:** make it optional with a default (connector owner) or update all callers to pass the value; check that pre-hook defaults are deployed in the target region
- **If JSON truncation:** reduce input size or split into multiple smaller arguments

## References

- [Docs: Building API Requests](https://docs.uipath.com/orchestrator/automation-cloud/latest/api-guide/building-api-requests)
- [Forum: StartJobs API call error code 400](https://forum.uipath.com/t/startjobs-api-call-error-code-400/469915)
