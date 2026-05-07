# Business Rule Implementation

This document defines the implementation boundary for business rule tasks.

## Model-owned implementation

The model may edit:

- `bpmn:businessRuleTask` or service task wrapper when that is the local pattern.
- Documented `Orchestrator.BusinessRules` `uipath:activity` shell.
- Input CDATA for facts using declared variables.
- Output mappings for rule result, matched rule, diagnostics, and outcome.
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
