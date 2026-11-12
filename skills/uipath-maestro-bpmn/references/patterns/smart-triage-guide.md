# Pattern: `smart-triage`

Heterogeneous inbound work is classified and dispatched to the right handling for its category.
Use it when volume is too high to sort by hand and the downstream paths are well defined.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **The trigger normalizes the payload.** Everything downstream reads one shape, so the same process serves email, tickets, forms, and webhooks.
  Routing never learns where the item came from.
- **Classification returns a category and a confidence.** Two values, so one gateway can decide whether to trust the answer and a second can act on it.
  A classifier returning only a category leaves nothing to gate on.
- **The human fallback rejoins the same route gateway.** Low-confidence items go to a person who picks the category, then dispatch through the identical exit.
  One dispatch point, not two, so adding a category is one branch rather than two.
- **Triage dispatches and ends.** Each category's real work lives in its own process.
  Keeping handling out of triage is what lets one triage process serve many downstreams without becoming all of them.

## Shape

AI-based is the base shape.
The categories are illustrative: one arm per category the domain actually has.

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('smart-triage')
  .name('SupportTriage')
  .flowMode('sequence')
  .var('routeCategory', 'string')
  .var('aiConfidence', 'number', { default: 0 })
  .startEvent('start', { name: 'Email received', message: 'SupportEmail' })
  .startAgent('classify', {
    name: 'Classify email',
    process: 'EmailClassifier',
    folder: 'Shared',
    outputs: { routeCategory: '=Category', aiConfidence: '=Confidence' },
  })
  // The confident arm is empty: it falls straight through to `route`.
  // The fallback arm sets the category, then falls through to the same `route`.
  .choose('confGate', [
    { when: '=vars.aiConfidence >= 0.85', label: 'Above floor', body: (b) => b },
    {
      otherwise: true,
      label: 'Below floor',
      body: (b) =>
        b.humanTask('manualTriage', {
          name: 'Pick a category',
          form: { fields: [], outcomes: ['Billing', 'Technical', 'Spam'] },
          outputs: { routeCategory: '=Action' },
        }),
    },
  ])
  .choose('route', [
    { when: '=vars.routeCategory == "Billing"', label: 'Billing', body: (b) => b.task('handleBilling').endEvent('routedBilling', { name: 'Billing routed' }) },
    { when: '=vars.routeCategory == "Technical"', label: 'Technical', body: (b) => b.task('handleTechnical').endEvent('routedTechnical', { name: 'Technical routed' }) },
    { otherwise: true, label: 'Spam', body: (b) => b.task('handleSpam').endEvent('routedSpam', { name: 'Spam discarded' }) },
  ])
  .build();
```

The load-bearing line is where `route` sits: AFTER `confGate`, not inside either of its arms.
Both arms fall through, so the builder joins them (`confGate_join`) and the one `route` gateway follows.
The natural nested form, a `route` choose inside the confident arm and a second copy after `manualTriage`, compiles, validates and passes `check`, and it is the shape this pattern exists to prevent.
Nothing in the loop reports it; the duplicated branches are the tell.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` with `message` | Entry |
| `classify` | `.startAgent()` | Mechanism · insertion point |
| `confGate` | `.choose()` | Mechanism |
| `manualTriage` | `.humanTask()` | Mechanism |
| `route` | `.choose()` after `confGate` | Mechanism |
| `handle*` | `.task()` | Placeholder |
| `routed*` | `.endEvent()`, named | Mechanism |

`0.85` is an illustrative floor.
Set it from how costly a misroute is against how much manual triage you can absorb.

| Variable | Type | Holds |
| --- | --- | --- |
| `itemData` | jsonSchema | The normalized item the classifier reads |
| `routeCategory` | string | The category to dispatch to |
| `aiConfidence` | number | Classifier confidence, 0–1 |
| `ruleMatched` | boolean | Rule-based and hybrid only |
| `triageNote` | string | The manual triager's note, if any |

`itemData` and `triageNote` are not in the sketch.
`itemData` is what the trigger delivers and `classify` reads as input; `triageNote` is a form field you add to `manualTriage` when triagers explain their choice.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| AI-based | — | The shape above |
| Rule-based | Are the categories decided by stable, auditable rules? | A business rule and a match gate replace the classifier and the confidence gate |
| Hybrid | Can rules handle the clear cases cheaply? | Rules first; the classifier catches the rest |

**Rule-based.** Replace `classify` with `.businessRule('applyRules', …)` and `confGate` with a `ruleGate` choose: `when: '=vars.ruleMatched == true'` falls through, `otherwise` holds `manualTriage`.
`route` still follows the gate.

**Hybrid.** Keep both.
`ruleGate`'s `otherwise` arm holds `classify` and the whole `confGate` choose, so an unmatched item reaches the classifier rather than a person, and every arm still falls through to the one `route`.

## What to bind

- **`classify`**: the node that classifies at runtime, typically `.startAgent()`.
  Place and bind it; never decide the categories or write classification logic while authoring.
  Its `outputs` keys are the process variables written (`routeCategory`, `aiConfidence`), and each value is an expression read against the agent's result (`'=Category'`, `'=Confidence'`, the agent's output arguments).
  `confGate` and `route` read those variables, so a key spelled as the agent's argument instead leaves them unset.
- **`applyRules`**: `.businessRule()`, a deployed BusinessRules package addressed by name; there is no in-file rule authoring.
  A decision's column reads `=result.<Decision>.<column>` ([Work dispatch](../bpmn-runtime.md#http-and-orchestrator-work)).
- **`extract`** (not drawn): Document Understanding, or any step that pulls the fields the classifier needs out of an unstructured source.
  Insert it before `classify`.
- **`handle*`**: see Adapting below; usually a message dispatch rather than work done here.
- **`manualTriage`**: `.humanTask()` as an inline form whose `outcomes` are the categories.
  Map `=Action` to `routeCategory`, the same variable `route` reads.
  Mapped anywhere else, low-confidence items dispatch on the classifier's original guess and the review changes nothing.

## Adapting it

Add or remove category arms to match the domain.
Each is one `when` on `route` plus its handler and end event.

Drop `extract` when the trigger already delivers structured fields.

The `handle*` nodes are the pattern's main decision.
Replacing each with a message that starts a separate process keeps triage thin, which is the intent.
Filling them inline makes triage own the handling for every category it routes, and that is what the shape is trying to avoid; it is a legitimate choice for one or two trivial categories.

## Composing

Each category's downstream is usually its own process, reached by message rather than nested; see [composing-guide.md](composing-guide.md#dispatched-by-message-to-a-separate-process).
`approval-chain` is a common downstream.
Add `failure-escalation` so a classifier or dispatch failure does not vanish.
