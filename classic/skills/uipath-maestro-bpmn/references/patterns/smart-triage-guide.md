# Pattern: `smart-triage`

Classify heterogeneous inbound work and dispatch each category to its defined path when volume exceeds manual sorting capacity.

## Why it works

Normalize every trigger to one downstream shape; return category and confidence so the gateway can accept or reject classification; send low-confidence items to human review and dispatch through the same exit using the human-selected category; keep category work in separate processes so triage stays reusable and thin. These four carry the shape. Change one and you are building something else.

## Shape

AI-based is the base shape. `A`/`B`/`C` are illustrative; create one branch per actual category.

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` + message event definition | Entry |
| `extract` | `bpmn:serviceTask` | Placeholder · insertion point |
| `classify` | `bpmn:serviceTask` | Mechanism |
| `conf_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `manual_triage` | `bpmn:userTask` | Mechanism |
| `route_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `handle_a..c` | `bpmn:serviceTask` | Placeholder |
| `routed_a..c` | `bpmn:endEvent` | Mechanism |

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `start` → `extract` → `classify` → `conf_gate` | | |
| `conf_gate` → `route_gate` | Above floor | `=vars.aiConfidence >= 0.85` |
| `conf_gate` → `manual_triage` | Below floor | `=vars.aiConfidence < 0.85` |
| `manual_triage` → `route_gate` | | |
| `route_gate` → `handle_a` | Category A | `=vars.routeCategory == "Category A"` |
| `route_gate` → `handle_b` | Category B | `=vars.routeCategory == "Category B"` |
| `route_gate` → `handle_c` | Category C | `=vars.routeCategory == "Category C"` |
| `handle_a..c` → `routed_a..c` | | |

`0.85` is illustrative; set the floor against misroute cost and manual-triage capacity.

| Variable | Type | Holds |
| --- | --- | --- |
| `itemData` | jsonSchema | The normalized item the classifier reads |
| `routeCategory` | string | The category to dispatch to |
| `aiConfidence` | double | Classifier confidence, 0–1 |
| `ruleMatched` | boolean | Rule-based and hybrid only |
| `triageNote` | string | The manual triager's note, if any |

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| AI-based | — | The shape above |
| Rule-based | Are categories decided by stable, auditable rules? | Business rule task and a match gateway |
| Hybrid | Can rules handle clear cases cheaply? | Rules first; classifier handles the rest |

**Rule-based.** Replace `classify` and `conf_gate` with `apply_rules` (`bpmn:businessRuleTask`) and `rule_gate` (`bpmn:exclusiveGateway`):

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `rule_gate` → `route_gate` | Matched | `=vars.ruleMatched == true` |
| `rule_gate` → `manual_triage` | No match | default |

**Hybrid.** Run rules first; send unmatched items to `classify`; send items unresolved by both to `manual_triage`.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `rule_gate` → `route_gate` | Matched | `=vars.ruleMatched == true` |
| `rule_gate` → `classify` | No match | default |
| `conf_gate` → `route_gate` | Above floor | as above |
| `conf_gate` → `manual_triage` | Below floor | as above |

## What to bind

- **`classify`** — Bind the runtime classifier, typically a UiPath agent job; never decide categories or write classification logic while authoring.
- **`apply_rules`** — Bind `Orchestrator.BusinessRules`. Rules live in a separate BusinessRules project (uipath-rules), deployed before BPMN binding (SKILL.md rule 17); do not author rules in-file. This applies to rule-based and hybrid variants.
- **`extract`** — Bind Document Understanding or another step that extracts classifier inputs from an unstructured source.
- **`handle_a..c`** — See Adapting; usually dispatch a message rather than perform work here.
- **`manual_triage`** — Bind `Actions.HITL` and bind its category output to `routeCategory`, the variable read by `route_gate`; otherwise low-confidence items dispatch using the classifier's original guess and review changes nothing.

Fetch payloads through [registry-workflow.md](../registry-workflow.md).

## Adapting it

Add or remove category branches as needed; each requires one `route_gate` condition, handler, and end event. Drop `extract` when the trigger already provides structured fields.

The `handle_*` nodes are the pattern's main decision: keep them as messages starting separate processes so triage stays thin. Inline handling is legitimate for one or two trivial categories, but makes triage own each category's work.

## Composing

Each category's downstream is usually a separate process reached by message rather than nesting; see [composing-guide.md](composing-guide.md#dispatched-by-message-to-a-separate-process). `approval-chain` is a common downstream. Add `failure-escalation` so classifier or dispatch failures do not vanish.
