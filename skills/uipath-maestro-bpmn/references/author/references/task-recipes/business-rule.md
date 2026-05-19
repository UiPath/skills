# Business Rule Recipe

Use this pass-2 recipe for confirmed business rule execution. In pass 1, model
the decision point and routing in the BPMN skeleton; apply this recipe after
the skeleton is chosen and the rule node should receive UiPath metadata.

The current supported implementation wrapper is `bpmn:businessRuleTask` with
`Orchestrator.BusinessRules`.

The model may draft:

- Business rule task wrapper, incoming/outgoing flows, and BPMN DI.
- Fact variables, result variables, diagnostics variables, and mappings.
- A gateway after the rule task when rule output drives routing.
- Retry, boundary error, or manual review paths when failures are recoverable.

CLI or operator must resolve:

- Rule identity, version, folder binding, and generated binding resources.
- Dynamic input and output schemas.

Do not represent a business rule as a generic service task in new XML unless preserving an imported file or matching an explicit product migration contract.
