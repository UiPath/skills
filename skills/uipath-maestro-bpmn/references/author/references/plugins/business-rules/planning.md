# Business Rule Planning

Use this reference when planning business rule execution from BPMN.

## When to use

- Evaluating rule tables or decision logic managed outside the BPMN diagram.
- Routing based on a rule result.
- Keeping business decisions separate from script code or gateway expressions.
- Combining rule evaluation with HITL review, queueing, RPA, or API workflow calls.

## Planning steps

1. Identify rule resource, input facts, output shape, and decision routes.
2. Decide whether rule failure should stop, retry, or route to manual review.
3. Declare variables for facts, result, diagnostics, and selected outcome.
4. Add a gateway after the rule task when result values drive routing.
5. Use placeholder-safe bindings until the rule resource is resolved.

## Model may draft

- Service task wrapper with documented `Orchestrator.BusinessRules` shell.
- Input/output mappings and post-rule gateway conditions.
- Retry and boundary error paths.
- Public-safe binding placeholders.

## Stop conditions

Stop before Operate when rule identity, input schema, output schema, version, or binding is unresolved.
