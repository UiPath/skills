# Pattern: `routing-triage`

Classify incoming emails, tickets, or claims and send each to its category handler. Use for high-volume work whose handling differs by type or urgency.

## Why it works

Each category has one shared handler and its own End recording the outcome; human-selected items rejoin that handler. Agent routing gates on confidence; rule routing sends unmatched items to a person. Nothing is dropped or guessed.
- **One set of category handlers.** Every route into a category, whether a rule,
  a confident agent, or a person, reaches the same handler for that category.
  A second dispatch path for human-picked items duplicates every handler.
- **The person rejoins, not replaces, the routing.** Low-confidence or
  unmatched items go to a person who picks the category, and the item is then
  handled exactly as if it had been routed automatically.

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

`classifyItem` returns `category` (one route), `confidence` (0 to 1), and `reason`. The form shows the category and reason. The canvas uses a quick form; pick the `hitl` variant the request names ([hitl.md](../hitl.md)).

**In the builder:** a branch arm or switch case may contain the step another path jumps to. Write canvas edges as follows:

1. `.branch('confidenceFloor', <confidence at or above the floor>, (ok) => ok.switch(...), (low) => low.stepToRef('pickCategory'))`.
2. `.switch('routeByCategory', out('classifyItem', 'category'), cases, (other) => other.stepSwitch('pickCategory', hitl({ ..., outcomes }), arms))`; each case runs its handler and `.return()`.
3. End each form arm with `.stepToRef('handle<Category>')`; name outcomes exactly as the switch case values.

## Variants

| Variant | Classifies with | Delta |
| --- | --- | --- |
| `rule` | Payload fields | Switch on item fields; no agent or confidence gate. Unmatched items go to the person |
| `ai` | An agent | The shape above |
| `hybrid` | Rules first, then an agent | Rule switch first; its `default` goes to the agent |

**`rule`.** `normalizeItem` (the source or field mapping) feeds `routeByRule`, a switch on a field such as `type`. Use when the item already carries its category.

**`hybrid`.** `routeByRule` first routes the unambiguous majority without an agent call; its `default` reaches `classifyItem`, which continues as in `ai`. Both switches use the same handlers: place the agent and remaining `ai` shape in `routeByRule`'s default arm, and have the category switch cases end `.stepToRef('handle<Category>')` into the rule switch's handlers.

## What to bind

- **`classifyItem`**: bind a published agent returning these fields, or use an `inlineAgent` with `returns`; never `mock()`. Include the category list in its prompt.
- **`handle<Category>`**: bind each category's downstream—such as a subflow, RPA workflow, connector, or queue item—chosen by rule 1. A category needing only recording goes directly to its End.
- **Switch cases and form outcomes** must list the same categories with identical names; change both together.

## Adapting it

If the flow already routes by a field, add only the agent and person behind the switch's `default`; this turns `rule` into `hybrid` without changing existing cases.
