# Business Rule Recipe

Use `bpmn:businessRuleTask` with `Orchestrator.BusinessRules`.

The model may draft:

- Business rule task wrapper, incoming/outgoing flows, and BPMN DI.
- Fact variables, result variables, diagnostics variables, and mappings.
- A gateway after the rule task when rule output drives routing.
- Retry, boundary error, or manual review paths when failures are recoverable.

CLI or operator must resolve:

- Rule identity, version, folder binding, and generated binding resources.
- Dynamic input and output schemas.

Do not represent a business rule as a generic service task in new XML unless preserving an imported file or matching an explicit product migration contract.
