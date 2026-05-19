---
confidence: high
---

# Expression Evaluation — Property Not Found

## Context

What this looks like:
- HTTP 400 with `Error evaluating expression in activity inputs for element: ...`
- `Property 'X' not found against object of type ExpressionDictionary`
- "Expression could not be parameterized" in parallel multi-instance subprocesses
- Job faulted due to null input during GUID parsing
- Ternary expressions failing in C# due to type erasure in Dynamic Expresso
- Underlying engine codes: `400300` (`InputVariablesEvaluationError`), `400301` (`ExpressionEvaluationError`), `400302` (`FlowExpressionEvaluationError` — gateway flows)

What can cause it:
- Expression references a variable/property that does not exist in the variable dictionary at evaluation time (typo, never assigned, conditionally assigned on a path not taken)
- Property casing — objects wrapped in `ExpressionDictionary` expose lowercase property accessors (e.g., `vars.error.detail` works, `vars.error.Detail` does not)
- Iterator references inside parallel multi-instance subprocesses were not supported historically — known workaround was to use embedded subprocess
- C# ternary type-erasure bug in Dynamic Expresso — known workaround is to switch to JS expressions (`=js:` prefix)
- Script Task iterator references unresolved by the engine (fix shipped in alpha and rolled forward)
- Upstream activity failed silently and left the consumed variable unset

What to look for:
- The exact property/variable name in `errorDetails`
- Whether the variable is initialized on every execution path that leads to this expression
- Whether the expression is C# or JS — both have distinct known bugs

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json` — `errorDetails` includes the full expression
2. Pull the variables snapshot at the failing element: `uip maestro <type> instance variables <instance-id> -f <folder-key> --parent-element-id <element-id> --output json` — confirm whether the referenced variable exists and what's defined
3. Walk element executions to find an upstream branch that should have initialized the variable: `uip maestro <type> instance element-executions <instance-id> -f <folder-key> --output json`
4. Inspect the expression in the BPMN: `uip maestro <type> instance asset <instance-id> -f <folder-key> --output json`

## Resolution

- **If typo / missing variable:** correct the name; use Maestro Expression Editor autocomplete (Ctrl+Space). The "Fix variables" dialog flags broken references
- **If casing mismatch on `ExpressionDictionary`:** access nested properties in lowercase (e.g., `vars.error.detail`)
- **If variable conditionally assigned:** initialize the variable on all paths or default it at the process start
- **If parallel multi-instance + iterator reference fails:** switch to embedded subprocess, or upgrade to a Maestro version where the parallel marker on the subprocess is supported
- **If C# ternary type-erasure:** rewrite as JS expression with `=js:` prefix
- **If null on GUID parse:** add a null check before parsing
- **If upstream silently failed:** fix the upstream task or add a boundary error event so the failure surfaces

## References

- [Docs: Variables and Expression Editor](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/variables-and-expression-editor)
