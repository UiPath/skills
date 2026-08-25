---
confidence: high
---

# Agent Traces Disappearing

## Context

What this looks like:
- Agent execution traces are missing
- Traces disappear after hours or days

What can cause it:
- Trace TTL (Time-To-Live) in AI Trust Layer policies is set to a short retention period (1 day or 7 days), automatically deleting traces

## Investigation

1. Check AI Trust Layer policies in the admin page for the Trace TTL setting

## Resolution

- Adjust or disable the Trace TTL setting in AI Trust Layer policies to retain traces for the required period
