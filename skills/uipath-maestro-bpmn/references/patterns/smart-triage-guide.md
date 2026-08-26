# Pattern: `smart-triage`

Heterogeneous inbound work is classified and dispatched to the right handling
for its category. Use it when volume is too high to sort by hand and the
downstream paths are well defined.

## Why it works

These four carry the shape. Change one and you are building something else.

- **The trigger normalizes the payload.** Everything downstream reads one shape,
  so the same process serves email, tickets, forms, and webhooks. Routing never
  learns where the item came from.
- **Classification returns a category and a confidence.** Two values, so one
  gateway can decide whether to trust the answer and a second can act on it.
  A classifier returning only a category leaves nothing to gate on.
- **The human fallback rejoins the same route gateway.** Low-confidence items go
  to a person who picks the category, then dispatch through the identical exit.
  One dispatch point, not two, so adding a category is one branch rather than
  two.
- **Triage dispatches and ends.** Each category's real work lives in its own
  process. Keeping handling out of triage is what lets one triage process serve
  many downstreams without becoming all of them.

## Shape

AI-based is the base shape. Categories `A`/`B`/`C` are illustrative — one branch
per category the domain actually has.

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

`0.85` is an illustrative floor. Set it from how costly a misroute is against
how much manual triage you can absorb.

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
| Rule-based | Are the categories decided by stable, auditable rules? | Business rule task and a match gateway |
| Hybrid | Can rules handle the clear cases cheaply? | Rules first, classifier catches the rest |

**Rule-based.** Replace `classify` and `conf_gate` with `apply_rules`
(`bpmn:businessRuleTask`) and `rule_gate` (`bpmn:exclusiveGateway`).

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `rule_gate` → `route_gate` | Matched | `=vars.ruleMatched == true` |
| `rule_gate` → `manual_triage` | No match | default |

**Hybrid.** Keep both. Rules run first; an unmatched item falls through to the
classifier rather than straight to a person, so only what neither resolves
reaches manual triage.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `rule_gate` → `route_gate` | Matched | `=vars.ruleMatched == true` |
| `rule_gate` → `classify` | No match | default |
| `conf_gate` → `route_gate` | Above floor | as above |
| `conf_gate` → `manual_triage` | Below floor | as above |

## What to bind

- **`classify`** — the node that classifies at runtime, typically a UiPath agent
  job. Place and bind it; never decide the categories or write classification
  logic while authoring.
- **`apply_rules`** — `Orchestrator.BusinessRules`. The rules are authored and
  uploaded to Orchestrator separately, and the BPMN references them; there is no
  in-file rule authoring. This applies to the rule-based and hybrid variants
  both.
- **`extract`** — Document Understanding, or any step that pulls the fields the
  classifier needs out of an unstructured source.
- **`handle_a..c`** — see Adapting below; usually a message dispatch rather than
  work done here.
- **`manual_triage`** — `Actions.HITL`.

Fetch payloads through [registry-workflow.md](../registry-workflow.md).

## Adapting it

Add or remove category branches to match the domain. Each is one condition on
`route_gate` plus its handler and end event.

Drop `extract` when the trigger already delivers structured fields.

The `handle_*` nodes are the pattern's main decision. Replacing each with a
message that starts a separate process keeps triage thin, which is the intent.
Filling them inline makes triage own the handling for every category it routes,
and that is what the shape is trying to avoid — but it is a legitimate choice for
one or two trivial categories.

## Composing

Each category's downstream is usually its own process, reached by message rather
than nested — see
[composing-guide.md](composing-guide.md#dispatched-by-message-to-a-separate-process).
`approval-chain` is a common downstream. Add `failure-escalation` so a
classifier or dispatch failure does not vanish.
