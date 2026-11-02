# Composing Patterns

Read this when a flow uses more than one pattern. A single pattern, built new or
inserted into a flow that already runs, needs only its own guide.

## Patterns are graph fragments

Each guide draws its pattern standalone. Two constrain placement, because the
trigger is the pattern's own:

- **`conversational-intake`** starts with `conversationTrigger()`, and
  **`voice-agents`' inbound variants** start with `voiceTrigger()`. Each begins
  the flow and replaces the manual trigger. Neither is inserted mid-flow.
- An outbound `voice-agents` call (`createOutgoingCall`) has no trigger and can
  sit anywhere.

## Four ways to join

Building from scratch with several patterns, the one that owns the trigger is
outermost and the rest go inside it.

### Inserted inline

The default. Wire the preceding step into the pattern's first node, and its
steps become part of the surrounding flow. Use it when the work belongs here and
nothing needs encapsulating, such as a confidence-gated review before an action
that already exists.

### Inside a loop body

`batch-ai`'s body can hold a whole pattern, so it runs once per item. The
pattern's End nodes become `body.continue()`, so the item ends and the loop
moves on; record the item's outcome in its result. Every step that can fail
inside the body keeps its own `.onError` continuation if one item must not stop
the batch. A step inside the body cannot be a `.stepToRef` target from outside
it (`REF_INTO_LOOP`).

### As a subflow

Put the pattern in a child flow and call it with `subflow()`
([subflow.md](../subflow.md)). Use it when the pattern needs its own scope, one
`.onError` around all of its steps, or a box that keeps the parent readable. A
child reads only what its `subflow(child, {...})` inputs pass in and returns only
its declared outputs.

### Inside a parallel arm

A pattern can be one arm of `.parallel()`, such as a review beside an
enrichment. The join waits for every arm, so an arm must not end in a human
task, an `action: 'End'` outcome, or a `.return()`; keep those after the join
([hitl.md](../hitl.md), [parallel-merge.md](../parallel-merge.md)).

## Adding a pattern to a flow that already runs

Insert only the part the flow lacks, and bind to what it already holds: an
existing agent, its confidence field, the action step it already calls. Each
guide's "Adapting it" names the commonest reduction. Everything the pattern does
not touch stays as it was; follow [brownfield.md](../brownfield.md) for the
decompile and merge loop.

## Worked combinations

| Combination | Outermost | How the rest join |
| --- | --- | --- |
| Batch of items, each decided by an agent with review | `batch-ai` | `ai-decision-human-review` in the loop body |
| Chat intake, then route the request | `conversational-intake` | `routing-triage` inline after the exit |
| Inbound call, then route the request | `voice-agents` `incoming-call` | `routing-triage` inline after `endCall` |
| Panel recommendation that a person signs off | `parallel-agents` | `ai-decision-human-review` inline after `synthesize` |
| Triage with review on one costly category | `routing-triage` | `ai-decision-human-review` inside that category's handler |
