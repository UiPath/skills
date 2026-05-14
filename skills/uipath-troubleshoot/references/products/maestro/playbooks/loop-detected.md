---
confidence: high
---

# Element Execution Loop Detected (400009)

## Context

What this looks like:
- HTTP 400, Maestro error code `400009` (`ElementExecutionLoopDetected`)
- Error message: `Possible loop detected: element 'X' has been executed more than 100 times. Failing the instance to prevent infinite loop.`
- Process was making progress, then engine kills the instance at iteration 101

What can cause it:
- Element exceeded `MaxElementExecutionCount` (default: 100)
- A control-loop exit condition never evaluates `true` (counter not incrementing, wrong comparison, variable not updated inside loop body)
- Legitimate large-batch workflow (e.g., 2000 queue items processed via gateway loop instead of marker)

What to look for:
- Element name and iteration count from `errorDetails`
- The exit condition expression — does it actually reference the variable that the loop body updates?
- Whether the workflow uses an explicit gateway loop or a multi-instance marker

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json` — captures element ID and iteration count
2. Walk element executions to see what each iteration produced: `uip maestro instance element-executions <instance-id> -f <folder-key> --output json`
3. Pull the variables snapshot near the loop element: `uip maestro instance variables <instance-id> -f <folder-key> --parent-element-id <element-id> --output json` — look for the loop counter / exit condition variable
4. Read the loop condition from the BPMN: `uip maestro instance asset <instance-id> -f <folder-key> --output json`

## Resolution

- **If counter not incrementing or wrong operator:** fix the loop body so the exit condition can eventually evaluate `true`
- **If legitimate large-batch processing:** redesign with a multi-instance marker (parallel or sequential) instead of a gateway loop — markers avoid loop detection entirely because there is no explicit loop element in the BPMN
- **If process genuinely needs >100 iterations of one element:** request the server-side `MaxElementExecutionCount` be raised via an environment-level feature flag (platform team)
- **If variable not updated inside loop body:** ensure the assignment happens before the gateway re-evaluates

## References

- [Docs: Looping](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/repetition)
- [Docs: BPMN Patterns and Practices](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/common-modeling-patterns)
