# Pattern: `conversational-intake`

A chat conversation is the front door. The flow drives every turn: wait for a
message, run the agent, loop back. The agent gathers what the process needs,
the flow starts the process or hands the person to a specialist, and it reports
back in the same conversation. Node details: [conversational.md](../conversational.md).

## Why it works

- **The flow owns the turn loop.** Wait for a message, run the conversational
  agent, then go back to the same wait. The agent answers one exchange per pass;
  the loop is what makes it a conversation.
- **A typed boolean exits the loop.** After every exchange something returns
  `readyToSubmit` (or `conversationComplete`), and a decision routes on it.
  Without an exit the loop never ends and every conversation leaves a suspended
  instance behind.
- **Work happens after the exit, then the flow reports back.** The process step
  runs once the request is complete, and `sendMessage` tells the person in the
  same conversation.

**The builder cannot type a conversational agent's output.** `conversationalAgent()`
has no `returns`, and one passed anyway is dropped without an error. The canvas
declares the exit fields on the conversational agent itself. In the builder,
every variant adds a turn check: an `inlineAgent` right after each
conversational agent that reads the transcript and the reply and returns the
fields the exit routes on. Route on the turn check, never on a field of the
conversational agent's output and never on text parsed from the reply.

## Shape

The `text-intake` variant:

| Step | Node | Builder | Role |
| --- | --- | --- | --- |
| `start` | `core.trigger.conversation` | `.trigger(conversationTrigger())` | Entry: replaces the manual trigger |
| `waitForMessage` | `uipath.conversational.wait-for-message` | `waitForMessage({ conversationId: out('start', 'conversationId') })` | Mechanism |
| `gatherRequest` | `uipath.agent.conversational` | `conversationalAgent({ settings: { context } })` | Mechanism |
| `checkIntake` | `uipath.agent.autonomous` | `inlineAgent({ inputs, returns })` | Mechanism: the turn check |
| `intakeComplete` | `core.logic.decision` | `.branch(...)` | Mechanism: the exit |
| `startProcess` | the process's node | per SKILL.md's node table | Placeholder |
| `reportBack` | `uipath.conversational.send-message` | `sendMessage(...)` | Mechanism |
| `endSubmitted` | `core.control.end` | `.return(...)` | Entry: the flow continues here when steps follow |

| From | Port | To |
| --- | --- | --- |
| `start` | `output` | `waitForMessage` |
| `waitForMessage` | `output` | `gatherRequest` |
| `gatherRequest` | `success` | `checkIntake` |
| `checkIntake` | `success` | `intakeComplete` |
| `intakeComplete` | not complete | `waitForMessage` (the turn loop) |
| `intakeComplete` | complete | `startProcess` |
| `startProcess` | | `reportBack` |
| `reportBack` | `output` | `endSubmitted` |

`gatherRequest` reads `out('waitForMessage', 'conversationContext')`; its prompt
asks one question at a time and confirms before finishing. `checkIntake` takes
`out('waitForMessage', 'conversationContext.messages')` and `out('gatherRequest')`
as inputs and returns `readyToSubmit` (boolean) and `requestSummary` (string).
`startProcess` reads `out('checkIntake')`. `reportBack` takes the trigger's
`conversationId` and the wait's `conversationContext.latestExchangeId`.

Write the loop as the canvas draws it, a back-edge:
`.branch('intakeComplete', js`$vars.checkIntake.output.readyToSubmit !== true`,
(more) => more.stepToRef('waitForMessage'))`, with the process step on the main
path after it. Not `.doWhile()`: steps inside its body are out of scope after
the loop, so `reportBack`'s read of the wait's exchange id draws a `validate`
warning (`EXPRESSION_DIAGNOSTIC`).

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| `assistant` | Is there no downstream process? | No process step or report; the turn check returns `conversationComplete` and the exit ends the flow |
| `text-intake` | (default) | The shape above |
| `handoff-to-specialist` | Does a specialist take over part of the conversation? | A switch after the general agent's turn check; the specialist runs its own loop |

**`handoff-to-specialist`.** The general agent's turn check returns
`needsSpecialist` and `conversationComplete`. `routeTurn`, a switch on those
fields, has a `specialist` case to `announceHandoff`, a `done` case to the End,
and a `default` back to the general agent's wait. `.switch()` takes one
discriminant, so fold the two fields into one string, with `<check>` the general
agent's turn check:
`` js`$vars.<check>.output.needsSpecialist === true ? 'specialist' : ($vars.<check>.output.conversationComplete === true ? 'done' : 'more')` ``.
`announceHandoff`
(`sendMessage`) tells the person who they are being connected to. Then
`waitSpecialist`, `specialistAgent` and its own turn check form a second loop,
which exits on `conversationComplete`. Add a specialist by adding a case with
its own announce, wait, agent and turn check.

## What to bind

- **The conversational agent**: model and system prompt.
- **Each turn check**: a model and a prompt that says when the exit condition
  holds. It decides at runtime; never decide it while authoring.
- **`startProcess`**: the process the request feeds, such as a subflow, an RPA
  workflow, an agentic process, or a queue item, chosen by rule 1.
- **`reportBack` content**: what the person reads once the request is submitted.

## Adapting it

A request that only answers questions is `assistant`; do not add a process step
the request did not name. Nothing local delivers a message: a green `validate`
proves the wiring, and the conversation itself is platform evidence
([conversational.md](../conversational.md#evidence-boundary)).
