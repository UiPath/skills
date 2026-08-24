# Composing Patterns

Read this when a process uses more than one pattern, or when adding a pattern to
a process that already exists.

## Patterns are graph fragments

Each guide draws its pattern standalone, so the shape opens with a start event.
That start event is an artifact of drawing it alone — it is not part of the
pattern. A pattern goes anywhere in a graph.

Keep the start event only when the pattern happens to begin the process. Author
it into the middle of an existing process and you drop the start event entirely.

Two entries are load-bearing and do constrain placement:

- **`queue-distribution`'s performer** — its start event carries the queue
  trigger, so the performer must begin the process. It cannot be inserted
  mid-process or nested in a subprocess.
- **`failure-escalation`** — an event subprocess with no sequence flows in or
  out. It is placed inside the container it guards and must sit there
  *directly*; wrapping it in another subprocess changes which failures reach
  it.

Both are engine behavior, not style.

## Four ways to join

Building from scratch with several patterns, the outermost one keeps its start
event and the rest go inside it.

### Inserted inline

The default. Drop the pattern's start event and wire the preceding step into its
first real node; its steps become part of the surrounding process.

Use it whenever the work belongs in this process and there is no reason to
encapsulate — adding a confidence-gated review partway through a process that
already runs.

### Nested as `bpmn:subProcess`

The pattern's start event becomes the subprocess's internal start event, and the
subprocess takes the sequence flows in and out.

Prefer this over inserting when you need what a container gives you: its own
variable scope, a multi-instance marker over the whole pattern, its own
`failure-escalation` net, or a collapsed box that keeps the parent readable.

Risk-tiered `approval-chain` already works this way internally: the standard and
extended chains are subprocesses the risk gate routes between.

### Placed, not wired

`failure-escalation` composes by placement alone. Drop the event subprocess into
the container whose failures it should catch and author no sequence flows to or
from it.

### Dispatched by message to a separate process

The downstream work becomes its own Maestro process, started by a message. Use
this when the downstream has its own lifecycle, its own trigger, or should scale
independently.

`smart-triage`'s per-category steps are placeholders for exactly this choice.
Replacing them with a dispatch keeps triage thin; filling them inline makes
triage own handling for every category it routes.

## Adding a pattern to a process that already runs

The process may already do part of what the pattern draws. Reuse what is there
instead of duplicating it: if the process already extracts and scores an item,
insert only the confidence gate and the review branch, not a second analyze
step. A partial pattern that reuses existing work beats a complete one bolted
alongside it.

Reuse existing variables the same way. Where a guide names a variable the
process already holds under another name, point the pattern's conditions at the
existing one rather than declaring a duplicate. Keep the guide's names only for
variables you are creating.

Everything the pattern does not touch stays untouched — element IDs, unknown
`uipath:*` payloads, imported connector data. Inserting a pattern is a surgical
edit, not a regeneration.

## Scoping the failure net

One net covers its whole container, including every subprocess nested under it,
because unhandled failures propagate outward container by container. A single
net at process level is the usual answer.

Add a second net inside a multi-instance iteration or a queue performer only
when per-item failures need per-item handling — when one bad item should be
recorded and the batch should continue. Without an inner net, the first failure
escalates through the process-level net and ends the instance.

See
[structural-bpmn.md](../structural-bpmn.md#choosing-an-error-handling-construct)
for choosing between a net, a boundary event, and node retry.

## Variables across a nesting boundary

A nested pattern's variables are scoped to its subprocess. Anything the parent
needs after the subprocess completes must be mapped out explicitly, and anything
the nested pattern reads from the parent must be mapped in. Two patterns that
both declare a variable of the same name do not share it across that boundary.

Where two patterns meet, keep each one's variable names rather than merging them
into a shared name — the guides' conditions reference those names directly.

## Worked combinations

| Combination | Outermost | How the rest join |
| --- | --- | --- |
| Batch of items, each AI-decided with review | `high-volume-batch` | `ai-decision-review` nested as the per-item subprocess |
| Triage inbound, then approve by category | `smart-triage` | `approval-chain` per category, dispatched by message |
| Queue performer with per-item error handling | `queue-distribution` performer | `failure-escalation` placed inside the performer |
| Add review to a process that already runs | the existing process | `ai-decision-review` inserted inline, no start event |
| Any production process | whichever owns the trigger | `failure-escalation` placed at process level |
