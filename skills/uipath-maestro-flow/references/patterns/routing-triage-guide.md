# Pattern: `routing-triage`

Incoming work (emails, tickets, claims) is classified and each item goes down the
path for its category. Use it for high-volume work whose handling differs by type
or urgency.

## Why it works

- **One set of category handlers.** Every route into a category, whether a rule,
  a confident agent, or a person, reaches the same handler for that category.
  A second dispatch path for human-picked items duplicates every handler.
- **The person rejoins, not replaces, the routing.** Low-confidence or
  unmatched items go to a person who picks the category, and the item is then
  handled exactly as if it had been routed automatically.
- **Every route has a floor.** Agent routing gates on confidence; rule routing
  sends what no rule matches to the person. Nothing is dropped and nothing is
  guessed.
- **Each category ends with its own outcome.** One End per category records
  where the item went.

## Shape

The `ai` variant:

| Step | Node | Builder | Role |
| --- | --- | --- | --- |
| `classifyItem` | `uipath.agent.autonomous` | `inlineAgent({ returns })` | Mechanism |
| `confidenceFloor` | `core.logic.decision` | `.branch(...)` | Mechanism |
| `routeByCategory` | `core.logic.switch` | `.switch(...)` | Mechanism: the one dispatch point |
| `pickCategory` | `uipath.human-in-the-loop.*` | `.stepSwitch(..., hitl({ outcomes }), arms)` | Mechanism: one outcome per category |
| `handle<Category>` | the downstream's node | per SKILL.md's node table | Placeholder, one per category |
| `end<Category>` | `core.control.end` | `.return(...)` | Mechanism, one per category |

| From | Port | To |
| --- | --- | --- |
| `classifyItem` | `success` | `confidenceFloor` |
| `confidenceFloor` | at or above the floor (`confidence >= 0.7`) | `routeByCategory` |
| `confidenceFloor` | below the floor | `pickCategory` |
| `routeByCategory` | `case-<id>`, one per category | `handle<Category>` |
| `routeByCategory` | `default` | `pickCategory` |
| `pickCategory` | `outcome-<category>` | `handle<Category>` |
| `handle<Category>` | | `end<Category>` |

`classifyItem` returns `category` (one of the routes), `confidence` (0 to 1) and
`reason`. The form shows the agent's category and reason. The canvas uses a
quick form; pick the `hitl` variant the request names ([hitl.md](../hitl.md)).

**In the builder,** a branch arm or a switch case can hold the step another
path jumps to, so the canvas edges are written as they are:

1. `.branch('confidenceFloor', <confidence at or above the floor>, (ok) => ok.switch(...), (low) => low.stepToRef('pickCategory'))`.
2. `.switch('routeByCategory', out('classifyItem', 'category'), cases, (other) => other.stepSwitch('pickCategory', hitl({ ..., outcomes }), arms))`,
   each case running its handler and its `.return()`.
3. Each form arm ends `.stepToRef('handle<Category>')`. Name the outcomes
   exactly as the switch's case values.

## Variants

| Variant | Classifies with | Delta |
| --- | --- | --- |
| `rule` | Payload fields | A switch on item fields; no agent, no confidence gate. Unmatched items go to the person |
| `ai` | An agent | The shape above |
| `hybrid` | Rules first, then an agent | A rule switch in front; its `default` goes to the agent |

**`rule`.** `normalizeItem` (the source or field mapping) feeds `routeByRule`,
a switch on a field such as `type`. Choose it when the item already carries its
category.

**`hybrid`.** `routeByRule` runs first and routes the unambiguous majority with no
agent call. Its `default` reaches `classifyItem`, which continues as in `ai`.
Both switches route into the same handlers: in the builder, the agent and the
rest of the `ai` shape sit in `routeByRule`'s default arm, and the category
switch's cases end `.stepToRef('handle<Category>')` into the rule switch's
handlers.

## What to bind

- **`classifyItem`**: a published agent that returns these fields, else an
  `inlineAgent` with `returns`, never `mock()`. Write its prompt with the
  category list.
- **`handle<Category>`**: each category's downstream, such as a subflow, an RPA
  workflow, a connector, or a queue item, chosen by rule 1. A category that only
  needs recording goes straight to its End.
- **Switch cases and form outcomes** list the same categories, with the same
  names. Change one and change the other.

## Adapting it

If the flow already routes by a field, add only the agent and the person behind
the switch's `default`; that turns `rule` into `hybrid` without touching the
existing cases.
