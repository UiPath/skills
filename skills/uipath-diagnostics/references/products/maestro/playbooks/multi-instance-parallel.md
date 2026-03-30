---
confidence: medium
---

# Multi-Instance Parallel Marker Issues

## Context

What this looks like:
- "Failed to evaluate the input collection variable for the marker element"
- Parallel steps failing
- Questions about how to loop over items

What can cause it:
- JS expression InvalidCastException (see marker-invalid-cast playbook for the specific bug)
- Batch concurrency limit exceeded — parallel markers have a limit of 50 items. For complex objects, use fewer than 50 due to a 2-second timeout risk
- NoneType errors in parallel steps — bug where `file.mime_type` is None causes crashes when `.lower()` is called (fix deployed to alpha/staging)
- Input collection variable is not of type array

What to look for:
- Check the expression language (JS vs C#) for the marker input
- Check the size and complexity of the input collection
- Check for null/None values in collection items

## Investigation

1. Check if the marker input collection uses JS or C# expressions
2. Check the collection size (>50 items for complex objects may timeout)
3. Check for null values in collection item properties (e.g., `file.mime_type`)
4. Verify the input collection variable is of type array

## Resolution

- **If JS expression error:** switch to C# expressions (see marker-invalid-cast playbook)
- **If collection too large:** reduce batch size below 50 for complex objects; simple items (strings, file references) support larger lists
- **If NoneType error:** add null checks for properties like `mime_type` before calling methods on them
- **To set up a loop:** add a multi-instance marker on the task node, configure the input collection (must be array type), use the iterator variable on inputs within the task
