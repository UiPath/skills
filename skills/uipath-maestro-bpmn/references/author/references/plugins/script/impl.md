# Script Implementation

This document defines the implementation boundary for script tasks.

## Model-owned implementation

The model may edit:

- `bpmn:scriptTask` with `scriptFormat="JavaScript"`.
- `bpmn:script` content in CDATA.
- `uipath:scriptVersion`.
- `uipath:mapping` for `args` input and outputs.
- Declared variables and JSON schemas used by the script.
- Boundary error paths.

## Implementation rules

- Keep script source deterministic and side-effect-light.
- Use `args` as the input object when that is the local convention.
- Return or map explicit outputs instead of mutating undeclared globals.
- Do not embed secrets, account data, URLs, or local paths.
- Do not use scripts as a substitute for connector enrichment or RPA work.

## Validation expectations

- Input variables exist and are readable.
- Output variables exist and are writable.
- Script CDATA is syntactically coherent.
- `uipath:scriptVersion` is present when required by the local contract.
