---
confidence: high
signatures:
  - kind: message
    value: "Package entry points definition is invalid"
    note: "deployment fails after adding DateTime input parameters to a BPMN start event"
---

# Deployment Error — DateTime Input Parameters

## Context

What this looks like:
- "Package entry points definition is invalid"
- Deployment fails after adding input parameters to a BPMN start event

What can cause it:
- DateTime data types on BPMN start event input parameters cause the package entry points definition to become invalid

## Investigation

1. Check the BPMN start event input parameters for DateTime data types

## Resolution

- Change all BPMN input parameters from DateTime to text/string data type
- Verify both deployment and debug mode work after changing parameter types
