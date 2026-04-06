---
confidence: high
---

# Multi-Instance Marker InvalidCastException

## Context

What this looks like:
- "Failed to evaluate the input collection variable for the marker element"
- InvalidCastException: System.Object[] to ExpressionList

What can cause it:
- Bug in Jint-based JS expression evaluator where JS arrays cannot be cast to the internal ExpressionList type expected by the BPMN engine (tracked via MST-7017)

## Investigation

1. Confirm the marker input collection uses a JavaScript expression
2. Check if the error is InvalidCastException referencing ExpressionList

## Resolution

- Switch the marker input collection expression from JavaScript to C# expressions
- Verify the parallel marker executes successfully with all list items
