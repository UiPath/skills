# Business Rule Implementation

This document defines the implementation boundary for business rule task recipes. Business rules are implemented as `bpmn:businessRuleTask`; see [task-recipes/business-rule.md](../../task-recipes/business-rule.md).

Use the canonical shell from
[shared/wrapper-shells.md](../../../../shared/wrapper-shells.md): a
`bpmn:businessRuleTask` containing `uipath:activity version="v1"` and nested
`uipath:type value="Orchestrator.BusinessRules" version="v1"`, with fact and
result movement in sibling `uipath:mapping`.
Do not author new business rule XML with legacy
`<uipath:activity type="Orchestrator.BusinessRules">` shorthand.

## Model-owned implementation

The model may edit:

- `bpmn:businessRuleTask` wrapper.
- Documented `Orchestrator.BusinessRules` `uipath:activity` shell.
- Input CDATA for facts in `uipath:mapping` using declared variables.
- `uipath:mapping` outputs for rule result, matched rule, diagnostics, and outcome.
- Gateway conditions that route by declared rule outputs.

## CLI or operator-owned implementation

The CLI or operator must resolve:

- Real business rule resource identity, version, and binding metadata.
- Dynamic input/output schemas.
- Generated package metadata.

## Validation expectations

- Rule binding resolves before upload/run.
- Facts match the resolved rule input contract.
- Result variables exist and route expressions are assignment-free.
- Fallback or manual review paths exist when rule failure is recoverable.
