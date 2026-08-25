---
confidence: medium
---

# Boundary Event and Duplicate Task Execution

## Context

What this looks like:
- Task running twice or duplicate agent runs
- Boundary events firing unexpectedly
- Error boundary events not logging incidents

What can cause it:
- Both Error and Timer boundary events attached to the same task — previously boundary events were not canceled when the attached task faulted (fixed in later releases)
- Error boundary events suppressing incident logging — this is expected BPMN behavior: boundary error events catch errors and redirect the flow, so incidents only appear for uncaught errors
- For Data Fabric tasks: error output (detail, category) is not exposed on boundary events unlike API Workflow tasks (known limitation)

What to look for:
- Check which boundary events are attached to the task
- Check if the task has both Error and Timer boundary events
- Check if the issue is duplicate execution or missing incident logging

## Investigation

1. Examine the BPMN process for boundary events on the affected task
2. Check if both Error and Timer boundary events are attached to the same task
3. Check if error boundary events are catching errors (expected behavior — no incident logged)
4. For Data Fabric tasks: check if error output fields are expected but not available

## Resolution

- **If duplicate execution due to boundary event bug:** update to the latest version containing the boundary event cancellation fix
- **If missing incidents:** this is expected BPMN behavior when error boundary events catch the error; incidents only appear for uncaught errors
- **If Data Fabric error output needed:** workaround is to use API Workflow tasks instead (Data Fabric boundary event error output is a known limitation)
